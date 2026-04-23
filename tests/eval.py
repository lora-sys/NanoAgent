#!/usr/bin/env -S uv run python
"""极简评估器 — prompt + expected + verify → 准确率

Usage:
    uv run python tests/eval.py                           # 全部任务
    uv run python tests/eval.py --task grep_class_defs   # 单任务
    uv run python tests/eval.py --verbose                 # 打印详情
    uv run python tests/eval.py --mock                    # mock 模式（快速验证）
"""

import argparse
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import NanoAgent
from core.tool_cache import get_tool_cache
from tests.eval_tasks import TASKS, Task


# ─── 验证器 ───────────────────────────────────────────────────────────────────

def verify_contains(response: str, expected: list[str]) -> bool:
    r = response.lower()
    return all(kw.lower() in r for kw in expected)

def verify_tools(result: dict, expected_tools: list[str]) -> bool:
    used = result.get("tools_used", [])
    if not expected_tools:
        return True
    # 每个期望工具都被用过
    return all(t in used for t in expected_tools)

def run_task(agent: NanoAgent, task: Task, verbose: bool = False) -> dict:
    cache = get_tool_cache()
    cache.clear()

    start = time.time()
    try:
        result = agent.run(task.prompt)
    except Exception as e:
        return {
            "task": task.name,
            "status": "error",
            "error": str(e),
            "passed": False,
            "time": time.time() - start,
        }

    elapsed = time.time() - start
    response = result.get("response", "") or ""
    tools = result.get("tools_used", [])

    if verbose:
        print(f"  → {response[:80]}{'...' if len(response) > 80 else ''}")
        print(f"  → tools: {tools}")

    # 验证
    if task.verify_type == "contains":
        passed = verify_contains(response, task.expected)
    elif task.verify_type == "tools":
        passed = verify_tools(result, task.expected_tools)
    else:
        passed = False

    return {
        "task": task.name,
        "status": result.get("status", ""),
        "passed": passed,
        "response": response[:200],
        "tools": tools,
        "time": round(elapsed, 1),
    }


# ─── 报告 ─────────────────────────────────────────────────────────────────────

def print_report(results: list[dict], total_time: float):
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    pct = 100 * passed / total if total else 0

    print()
    print("=" * 60)
    print(f"  准确率: {passed}/{total} ({pct:.1f}%)  耗时: {total_time:.1f}s")
    print("=" * 60)

    for r in results:
        icon = "✅" if r["passed"] else "❌"
        print(f"  {icon} {r['task']:<35} {r['time']:>5}s  tools={r['tools']}")

    print()
    # 按功能维度汇总
    groups = {}
    for r in results:
        name = r["task"]
        if "_file_" in name:
            feat = "file"
        elif "_files" in name or name.startswith("list_"):
            feat = "dir"
        elif name.startswith("grep_"):
            feat = "grep"
        elif name.startswith("run_bash"):
            feat = "bash"
        elif name.startswith("multi_"):
            feat = "multi"
        elif name.startswith("lifecycle"):
            feat = "lifecycle"
        elif name.startswith("chain_"):
            feat = "chain"
        elif name.startswith("observability"):
            feat = "observe"
        elif name.startswith("cache_"):
            feat = "cache"
        else:
            feat = "other"
        groups.setdefault(feat, []).append(r)

    for feat, rs in groups.items():
        p = sum(1 for r in rs if r["passed"])
        t = len(rs)
        bar = "█" * p + "░" * (t - p)
        print(f"  {feat:<10} {p}/{t} {bar}")


def save_results(results: list[dict], total_time: float, out: Path):
    out.parent.mkdir(parents=True, exist_ok=True)
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    json.dump({
        "accuracy": round(100 * passed / total, 1) if total else 0,
        "passed": passed,
        "total": total,
        "total_time_s": round(total_time, 1),
        "results": results,
    }, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n💾 结果: {out}")


# ─── 主入口 ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="NanoAgent 评估器")
    parser.add_argument("--task", help="只跑指定任务")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--mock", action="store_true", help="mock 模式（不调 API）")
    parser.add_argument("--output", "-o", default=".spec/eval_results.json")
    args = parser.parse_args()

    # 过滤任务
    tasks = [t for t in TASKS if not args.task or t.name == args.task]
    if not tasks:
        print(f"未找到任务: {args.task}")
        sys.exit(1)

    print(f"\n{'[MOCK]' if args.mock else ''} 评估: {len(tasks)} 个任务")
    print("-" * 60)

    agent = NanoAgent()
    if args.mock:
        agent.llm.mock_enabled = True

    results = []
    start = time.time()

    for i, task in enumerate(tasks):
        print(f"[{i+1}/{len(tasks)}] {task.name}...", end=" ", flush=True)
        r = run_task(agent, task, args.verbose)
        results.append(r)
        print(f"{'✅' if r['passed'] else '❌'} {r['time']}s")

    total_time = time.time() - start
    print_report(results, total_time)
    save_results(results, total_time, Path(args.output))


if __name__ == "__main__":
    main()