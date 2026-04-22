"""集成评估脚本 — 每个功能 3 个提示词，real API

Usage:
    uv run python tests/run_integration_eval.py
"""

import sys
import time
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent import NanoAgent
from core.evaluation import Task, Runner, Difficulty, VerifyType


# ─── 评估任务定义 ───────────────────────────────────────────────────────────

TASKS = [

    # ── 1. 文件读取 ────────────────────────────────────────────────────────
    Task(
        name="read_file_readme",
        description="读取 README.md",
        prompt="读取项目根目录的 README.md 文件，告诉我这个项目叫什么名字",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["NanoAgent"],
        expected_tools=["read_file"],
    ),
    Task(
        name="read_file_pyproject",
        description="读取 pyproject.toml",
        prompt="读取 pyproject.toml 文件，告诉我项目名称和版本号",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["nanoagent"],
        expected_tools=["read_file"],
    ),
    Task(
        name="read_file_core_agent",
        description="读取核心文件",
        prompt="读取 core/agent.py 的前 20 行代码",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["NanoAgent"],
        expected_tools=["read_file"],
    ),

    # ── 2. 目录列表 ────────────────────────────────────────────────────────
    Task(
        name="list_files_project",
        description="列出项目根目录",
        prompt="列出项目根目录的所有文件和文件夹",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.TOOLS,
        expected="",
        expected_tools=["list_files"],
    ),
    Task(
        name="list_files_examples",
        description="列出 examples 目录",
        prompt="列出 examples/ 目录下的所有文件",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["examples"],
        expected_tools=["list_files"],
    ),
    Task(
        name="list_files_tests",
        description="列出 tests 目录结构",
        prompt="列出 tests/ 目录下有哪些测试文件",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["tests"],
        expected_tools=["list_files"],
    ),

    # ── 3. Grep 搜索 ──────────────────────────────────────────────────────
    Task(
        name="grep_function_defs",
        description="搜索函数定义",
        prompt="在 core/ 目录下搜索所有以 'def ' 开头的行（函数定义），列出前 5 个",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["def"],
        expected_tools=["grep"],
    ),
    Task(
        name="grep_imports",
        description="搜索 import 语句",
        prompt="在 core/agent.py 中搜索所有 import 语句",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["import"],
        expected_tools=["grep"],
    ),
    Task(
        name="grep_class_defs",
        description="搜索类定义",
        prompt="在 tools/ 目录下搜索包含 'class ' 的行（类定义）",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["class"],
        expected_tools=["grep"],
    ),

    # ── 4. Bash 命令 ───────────────────────────────────────────────────────
    Task(
        name="run_bash_pwd",
        description="运行 pwd",
        prompt="运行 'pwd' 命令，显示当前工作目录",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.TOOLS,
        expected="",
        expected_tools=["run_bash"],
    ),
    Task(
        name="run_bash_ls",
        description="运行 ls",
        prompt="运行 'ls -la' 命令，列出目录内容",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.TOOLS,
        expected="",
        expected_tools=["run_bash"],
    ),
    Task(
        name="run_bash_git_status",
        description="运行 git status",
        prompt="运行 'git status --short' 命令，显示 git 状态",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.TOOLS,
        expected="",
        expected_tools=["run_bash"],
    ),

    # ── 5. 多工具组合 ───────────────────────────────────────────────────────
    Task(
        name="multi_read_and_list",
        description="读取 + 列表组合",
        prompt="先列出 tests/ 目录，再读取其中的一个 .py 文件",
        difficulty=Difficulty.INTERMEDIATE,
        verify_type=VerifyType.TOOLS,
        expected="",
        expected_tools=["list_files", "read_file"],
    ),
    Task(
        name="multi_search_and_read",
        description="搜索 + 读取组合",
        prompt="在 core/ 下搜索包含 'class NanoAgent' 的文件，然后读取该文件",
        difficulty=Difficulty.INTERMEDIATE,
        verify_type=VerifyType.TOOLS,
        expected="",
        expected_tools=["grep", "read_file"],
    ),
    Task(
        name="multi_list_and_grep",
        description="列表 + 搜索组合",
        prompt="列出 tools/ 目录，然后在其中搜索包含 'def ' 的行",
        difficulty=Difficulty.INTERMEDIATE,
        verify_type=VerifyType.TOOLS,
        expected="",
        expected_tools=["list_files", "grep"],
    ),

    # ── 6. 生命周期 ───────────────────────────────────────────────────────
    Task(
        name="lifecycle_single_turn",
        description="单轮对话生命周期",
        prompt="简单回复：你好",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["你好", "nanoagent", "NanoAgent"],
        expected_tools=[],
    ),
    Task(
        name="lifecycle_with_tool",
        description="带工具调用的生命周期",
        prompt="读取 README.md 并告诉我项目名称",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["NanoAgent"],
        expected_tools=["read_file"],
    ),
    Task(
        name="lifecycle_multi_tool",
        description="多工具生命周期",
        prompt="列出 tests/ 目录，然后读取 README.md",
        difficulty=Difficulty.INTERMEDIATE,
        verify_type=VerifyType.TOOLS,
        expected="",
        expected_tools=["list_files", "read_file"],
    ),

    # ── 7. Chain 模式 ───────────────────────────────────────────────────────
    Task(
        name="chain_mode_analysis",
        description="提示链模式 - 架构分析",
        prompt="提示链 帮我分析 nanoagent 项目的整体架构",
        difficulty=Difficulty.INTERMEDIATE,
        verify_type=VerifyType.CONTAINS,
        expected=["core", "agent", "模块"],
        expected_tools=[],
    ),
    Task(
        name="chain_mode_summary",
        description="提示链模式 - 项目总结",
        prompt="提示链 总结这个项目的核心功能和设计原则",
        difficulty=Difficulty.INTERMEDIATE,
        verify_type=VerifyType.CONTAINS,
        expected=["NanoAgent", "功能", "设计"],
        expected_tools=[],
    ),
    Task(
        name="chain_mode_structure",
        description="提示链模式 - 结构设计",
        prompt="提示链 分析 core/ 目录的代码结构设计",
        difficulty=Difficulty.INTERMEDIATE,
        verify_type=VerifyType.CONTAINS,
        expected=["core", "模块", "代码"],
        expected_tools=[],
    ),

    # ── 8. 可观测性 / 追踪 ──────────────────────────────────────────────────
    Task(
        name="observability_basic",
        description="基本追踪",
        prompt="列出 tests/ 目录的内容",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.TOOLS,
        expected="",
        expected_tools=["list_files"],
    ),
    Task(
        name="observability_grep",
        description="Grep 追踪",
        prompt="在 core/ 下搜索包含 'lifecycle' 的文件",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["lifecycle", "core"],
        expected_tools=["grep"],
    ),
    Task(
        name="observability_read",
        description="Read 追踪",
        prompt="读取 README.md 的第一段",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["NanoAgent"],
        expected_tools=["read_file"],
    ),

    # ── 9. Tool Result Cache ───────────────────────────────────────────────
    Task(
        name="cache_grep_result",
        description="grep 结果缓存摘要",
        prompt="在 core/ 下搜索 'class ' 关键字",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["class"],
        expected_tools=["grep"],
    ),
    Task(
        name="cache_read_result",
        description="read_file 结果缓存摘要",
        prompt="读取 core/agent.py 的前 5 行",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.CONTAINS,
        expected=["NanoAgent"],
        expected_tools=["read_file"],
    ),
    Task(
        name="cache_list_result",
        description="list_files 结果缓存摘要",
        prompt="列出项目根目录的所有内容",
        difficulty=Difficulty.BASIC,
        verify_type=VerifyType.TOOLS,
        expected="",
        expected_tools=["list_files"],
    ),
]


def group_by_feature(tasks: list[Task]) -> dict[str, list[Task]]:
    groups = {}
    for t in tasks:
        name = t.name
        if "_file_" in name or "_files" in name:
            feat = "文件读写 (read_file, list_files)"
        elif name.startswith("list_"):
            feat = "目录列表 (list_files)"
        elif name.startswith("grep_"):
            feat = "代码搜索 (grep)"
        elif name.startswith("run_bash"):
            feat = "Bash 命令 (run_bash)"
        elif name.startswith("multi_"):
            feat = "多工具组合"
        elif name.startswith("lifecycle"):
            feat = "生命周期事件"
        elif name.startswith("chain_"):
            feat = "Chain 提示链模式"
        elif name.startswith("observability"):
            feat = "可观测性 / 追踪"
        elif name.startswith("cache_"):
            feat = "Tool Result Cache"
        else:
            feat = "其他"
        groups.setdefault(feat, []).append(t)
    return groups


def check_trace_created(trace_path: Path) -> bool:
    """检查追踪数据库中是否有新的记录"""
    if not trace_path.exists():
        return False
    import sqlite3
    try:
        conn = sqlite3.connect(trace_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM traces")
        count = cur.fetchone()[0]
        conn.close()
        return count > 0
    except Exception:
        return False


def main():
    print("=" * 80)
    print("NanoAgent 集成评估 — Real API")
    print("=" * 80)

    agent = NanoAgent()
    runner = Runner(agent)
    trace_path = Path.home() / ".nanoagent" / "traces.db"

    # 记录运行前 trace 数
    traces_before = 0
    if trace_path.exists():
        import sqlite3
        conn = sqlite3.connect(trace_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM traces")
        traces_before = cur.fetchone()[0]
        conn.close()

    results = runner.run_suite(TASKS)

    # ─── 分析 ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("📊 评估报告")
    print("=" * 80)

    summary = results["summary"]
    print(f"总任务数: {summary.get('total_tasks', 0)}")
    print(f"通过数:   {summary.get('successful_tasks', 0)}")
    print(f"成功率:   {summary.get('success_rate', 0):.1%}")
    print(f"总耗时:   {summary.get('total_time', 0):.1f}s")
    print()

    # 按功能分组统计
    groups = group_by_feature(TASKS)
    print("─── 功能维度 ───")
    for feat, feat_tasks in groups.items():
        feat_results = [r for r in runner.results for t in feat_tasks if t.name == r["task"]["name"]]
        passed = sum(1 for r in feat_results if r.get("verification", {}).get("passed", False))
        total = len(feat_results)
        bar = "█" * passed + "░" * (total - passed)
        print(f"  {feat:<40} {passed}/{total} {bar}")
        for r in feat_results:
            status = "✅" if r.get("verification", {}).get("passed") else "❌"
            name = r["task"]["name"]
            tools = r.get("result", {}).get("tools_used", [])
            print(f"    {status} {name:<35} tools={tools}")

    # 工具使用统计
    print("\n─── 工具使用 ───")
    tool_usage = {}
    for r in runner.results:
        for tool in r.get("result", {}).get("tools_used", []):
            tool_usage[tool] = tool_usage.get(tool, 0) + 1
    for tool, count in sorted(tool_usage.items(), key=lambda x: -x[1]):
        print(f"  {tool:<20} {count:>3} 次")

    # 追踪验证
    print("\n─── 追踪验证 ───")
    if trace_path.exists():
        import sqlite3
        conn = sqlite3.connect(trace_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM traces")
        traces_after = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM llm_calls")
        llm_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tool_calls")
        tool_count = cur.fetchone()[0]
        conn.close()
        print(f"  traces: {traces_before} → {traces_after} (+{traces_after - traces_before})")
        print(f"  llm_calls: {llm_count}")
        print(f"  tool_calls: {tool_count}")
    else:
        print("  traces.db 不存在")

    # 生命周期验证
    print("\n─── 生命周期 ───")
    lc = agent.lifecycle
    print(f"  depth: {lc._depth}")
    print(f"  total_turns: {lc.get_turn_number()}")
    print(f"  total_tools: {lc.get_totals()[1]}")

    # 保存结果
    out_file = Path(".spec/integration_eval_results.json")
    out_file.parent.mkdir(exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": summary,
            "results": [
                {
                    "task": r["task"],
                    "passed": r.get("verification", {}).get("passed", False),
                    "tools_used": r.get("result", {}).get("tools_used", []),
                    "status": r.get("result", {}).get("status", ""),
                    "error": r.get("error", ""),
                }
                for r in runner.results
            ],
        }, f, ensure_ascii=False, indent=2)
    print(f"\n💾 详细结果已保存: {out_file}")


if __name__ == "__main__":
    main()
