#!/usr/bin/env -S uv run python
"""RAG 评测器 — 针对 NanoAgent RAG Demo 的专项评测

测试内容：
- 文档内容问答（有明确答案）
- Hallucination 测试（文档中不存在的内容）
- 引用精度测试

Usage:
    uv run python tests/eval_rag.py                       # 全部任务
    uv run python tests/eval_rag.py --task rag_nanoagent_what  # 单任务
    uv run python tests/eval_rag.py -v                   # 详细输出
    uv run python tests/eval_rag.py --reset              # 重置并重新上传文档
"""

import argparse
import json
import time
import sys
import requests
from pathlib import Path

# 确保 examples 模块可导入
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.eval_tasks_rag import TASKS_RAG, RAGTask

SERVER = "http://localhost:8765"
FIXTURE = (
    Path(__file__).parent.parent / "examples/rag_demo/tests/fixtures/rag_test_doc.txt"
)
RESULTS_OUT = Path(".spec/rag_eval_results.json")


# ─── 验证器 ───────────────────────────────────────────────────────────────────


def verify_grounded(response_json: dict, task: RAGTask) -> tuple[bool, str]:
    """验证有答案的问题：关键词存在 + 有效引用 + 分数够高."""
    answer = response_json.get("answer", "")
    citations = response_json.get("citations", [])

    reasons = []

    # 1. 检查是否有引用
    if len(citations) < task.min_citations:
        return False, f"引用不足: {len(citations)} < {task.min_citations}"
    reasons.append(f"citations={len(citations)}")

    # 2. 检查引用分数
    scores = [c["score"] for c in citations]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    if task.min_avg_score > 0 and avg_score < task.min_avg_score:
        return False, f"平均分数不足: {avg_score:.3f} < {task.min_avg_score}"
    reasons.append(f"avg_score={avg_score:.3f}")

    # 3. 关键词匹配（允许同义词，部分匹配也给分）
    # 使用松弛匹配：关键词的任何子串匹配都算
    answer_lower = answer.lower()
    matched = []
    for kw in task.expected_keywords:
        kw_lower = kw.lower()
        parts = kw_lower.split()
        if kw_lower in answer_lower or any(p in answer_lower for p in parts):
            matched.append(kw)
    match_rate = (
        len(matched) / len(task.expected_keywords) if task.expected_keywords else 1.0
    )

    if match_rate < 0.5:  # 至少 50% 关键词匹配
        return (
            False,
            f"关键词匹配率不足: {match_rate:.0%} ({len(matched)}/{len(task.expected_keywords)})",
        )
    reasons.append(f"keyword_match={match_rate:.0%}({matched})")

    return True, " | ".join(reasons)


def verify_no_citation(response_json: dict, task: RAGTask) -> tuple[bool, str]:
    """验证无答案的问题：应该无有效引用或返回 '未找到'.

    通过标准：
    - citations 为空，或
    - 所有 citation score 都低于阈值，或
    - answer 包含"未找到"字样
    """
    answer = response_json.get("answer", "")
    citations = response_json.get("citations", [])

    if "未找到" in answer or "没有" in answer or "不包含" in answer:
        return True, "正确拒绝（未找到提示）"

    # 检查是否所有引用都低于有效阈值
    if citations:
        threshold = task.rag_min_score
        low_scores = [c["score"] for c in citations if c["score"] < threshold]
        if len(low_scores) == len(citations):
            return True, f"正确拒绝（{len(citations)} 个低分引用 < {threshold}）"

    # 如果有有效引用和高分 → 失败（幻觉）
    high_score_citations = [c for c in citations if c["score"] >= task.rag_min_score]
    if high_score_citations:
        return (
            False,
            f"幻觉检测！文档中不存在但有 {len(high_score_citations)} 个有效引用",
        )

    return True, "无有效引用"


# ─── RAG 客户端 ───────────────────────────────────────────────────────────────


def ensure_document_uploaded() -> bool:
    """确保测试文档已上传（重置后重新上传）."""
    try:
        resp = requests.get(f"{SERVER}/files", timeout=5)
        docs = resp.json().get("docs", [])
        for d in docs:
            if d["filename"] == FIXTURE.name:
                return True  # 已上传
    except Exception:
        pass

    # 需要上传
    try:
        with open(FIXTURE, "rb") as f:
            resp = requests.post(
                f"{SERVER}/upload",
                files={"file": (FIXTURE.name, f, "text/plain")},
                timeout=30,
            )
        return resp.status_code == 200
    except Exception as e:
        print(f"  ⚠️ 上传文档失败: {e}")
        return False


def reset_and_prepare() -> bool:
    """重置状态并准备文档."""
    try:
        requests.post(f"{SERVER}/reset", timeout=5)
        time.sleep(0.5)
        return ensure_document_uploaded()
    except Exception as e:
        print(f"  ⚠️ Reset 失败: {e}")
        return False


def query_rag(question: str, top_k: int = 5, min_score: float = 0.3) -> dict:
    """调用 RAG query 端点."""
    resp = requests.post(
        f"{SERVER}/query",
        params={"question": question, "top_k": top_k, "min_score": min_score},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


# ─── 单任务运行 ────────────────────────────────────────────────────────────────


def run_task(task: RAGTask, verbose: bool = False) -> dict:
    start = time.time()
    try:
        response = query_rag(
            question=task.prompt,
            top_k=task.rag_top_k,
            min_score=task.rag_min_score,
        )
    except Exception as e:
        return {
            "task": task.name,
            "status": "error",
            "error": str(e),
            "passed": False,
            "time": time.time() - start,
        }

    elapsed = time.time() - start

    # 验证
    if task.verify_type == "rag_grounded":
        passed, reason = verify_grounded(response, task)
    elif task.verify_type == "rag_no_citation":
        passed, reason = verify_no_citation(response, task)
    else:
        passed, reason = False, f"未知 verify_type: {task.verify_type}"

    if verbose:
        citations = response.get("citations", [])
        print(f"  → {reason}")
        print(
            f"  → citations: {len(citations)}, answer: {response.get('answer', '')[:80]}"
        )

    return {
        "task": task.name,
        "status": "ok",
        "passed": passed,
        "reason": reason,
        "citations_count": len(response.get("citations", [])),
        "answer_preview": response.get("answer", "")[:100],
        "time": round(elapsed, 1),
    }


# ─── 报告 ──────────────────────────────────────────────────────────────────────


def print_report(results: list[dict], total_time: float):
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    pct = 100 * passed / total if total else 0

    print()
    print("=" * 60)
    print(f"  RAG 准确率: {passed}/{total} ({pct:.1f}%)  耗时: {total_time:.1f}s")
    print("=" * 60)

    # 按类型分组
    grounded = [
        r
        for r in results
        if "nanoagent" in r["task"]
        or "core" in r["task"]
        or "llm" in r["task"]
        or "tool" in r["task"]
        or "lifecycle" in r["task"]
        or "observability" in r["task"]
    ]
    halluc = [r for r in results if "hallucination" in r["task"]]
    partial = [r for r in results if "partial" in r["task"]]

    for r in results:
        icon = "✅" if r["passed"] else "❌"
        extra = f" ({r.get('reason', '')})" if not r["passed"] else ""
        print(f"  {icon} {r['task']:<35} {r['time']:>5}s{extra}")

    print()
    if grounded:
        p = sum(1 for r in grounded if r["passed"])
        print(f"  grounded   {p}/{len(grounded)} {'█' * p}{'░' * (len(grounded) - p)}")
    if halluc:
        p = sum(1 for r in halluc if r["passed"])
        print(f"  hallucination {p}/{len(halluc)} {'█' * p}{'░' * (len(halluc) - p)}")
    if partial:
        p = sum(1 for r in partial if r["passed"])
        print(f"  partial    {p}/{len(partial)} {'█' * p}{'░' * (len(partial) - p)}")

    # 额外指标
    citation_scores = [
        c
        for r in results
        if r.get("citations_count", 0) > 0
        for c in [r["citations_count"]]
    ]
    halluc_false = sum(1 for r in halluc if not r["passed"])

    print()
    if citation_scores:
        avg_cite = sum(citation_scores) / len(citation_scores)
        print(f"  平均引用数: {avg_cite:.1f}")
    halluc_count = len(halluc)
    print(f"  幻觉误报: {halluc_false}/{halluc_count} (低越好)")


def save_results(results: list[dict], total_time: float):
    RESULTS_OUT.parent.mkdir(parents=True, exist_ok=True)
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    json.dump(
        {
            "accuracy": round(100 * passed / total, 1) if total else 0,
            "passed": passed,
            "total": total,
            "total_time_s": round(total_time, 1),
            "results": results,
        },
        open(RESULTS_OUT, "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2,
    )
    print(f"\n💾 结果: {RESULTS_OUT}")


# ─── 主入口 ───────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="NanoAgent RAG 评测器")
    parser.add_argument("--task", help="只跑指定任务")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument(
        "--reset", action="store_true", help="重置 RAG 状态并重新上传文档"
    )
    args = parser.parse_args()

    # 检查 server 是否运行
    try:
        requests.get(f"{SERVER}/", timeout=5)
    except Exception:
        print("❌ RAG server 未运行！请先启动：")
        print("   uv run python -m examples.rag_demo.server serve --port 8765")
        sys.exit(1)

    # 重置 + 准备文档
    if args.reset or True:  # 始终重置确保干净状态
        print("🔄 重置 RAG 状态...")
        ok = reset_and_prepare()
        if not ok:
            print("❌ 文档上传失败，请检查 server 日志")
            sys.exit(1)
        print("  ✅ 文档已上传")

    # 过滤任务
    tasks = [t for t in TASKS_RAG if not args.task or t.name == args.task]
    if not tasks:
        print(f"未找到任务: {args.task}")
        sys.exit(1)

    print(f"\n评估: {len(tasks)} 个 RAG 任务")
    print("-" * 60)

    results = []
    start = time.time()

    for i, task in enumerate(tasks):
        print(f"[{i + 1}/{len(tasks)}] {task.name}...", end=" ", flush=True)
        r = run_task(task, args.verbose)
        results.append(r)
        icon = "✅" if r["passed"] else "❌"
        reason = f" ({r.get('reason', '')})" if not r["passed"] else ""
        print(f"{icon} {r['time']}s{reason}")

    total_time = time.time() - start
    print_report(results, total_time)
    save_results(results, total_time)


if __name__ == "__main__":
    main()
