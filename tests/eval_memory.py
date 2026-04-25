"""Memory eval runner — 验证记忆系统功能."""

import argparse
import sys
import json
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.eval_tasks_memory import get_memory_tasks, MemoryTask


def verify_result(task: MemoryTask, response: str, tools_used: list[str]) -> bool:
    """验证任务结果。"""
    if task.verify_type == "contains":
        if isinstance(task.expected, list):
            return all(kw.lower() in response.lower() for kw in task.expected)
        return task.expected.lower() in response.lower()

    elif task.verify_type == "tools":
        return all(tool in tools_used for tool in task.expected_tools)

    elif task.verify_type == "exact":
        return response.strip() == task.expected.strip()

    return True


def run_memory_eval(mock: bool = False, verbose: bool = False) -> dict:
    """运行记忆系统评估。"""
    from core.memory import get_memory_manager, reset_memory_manager, MemoryManager
    from core.memory.stores import InMemoryStore

    results = []
    tasks = get_memory_tasks()

    # Run tests with fresh memory for each independent test
    for task in tasks:
        try:
            # Each task gets fresh memory state
            reset_memory_manager()
            mm = get_memory_manager()

            # Pre-flight: set up state needed for this task
            if task.name == "memory_preference_get":
                # Need to set name first
                mm.get_store("preference").set_preference("name", "Alice")
            elif task.name == "memory_long_term_recall":
                # Need to store first
                mm.get_store("long_term").set("core_modules", "agent, tools, llm")
            elif task.name == "memory_working_recall":
                # Need to store first
                mm.get_store("working").set("progress", "完成了第一步")
            elif task.name == "memory_forget":
                # Set something to forget
                mm.get_store("long_term").set("name", "Bob")

            # Execute the task
            result = _execute_task(mm, task)

            # Verify
            tools_used = []
            passed = verify_result(task, str(result), tools_used)

            results.append({
                "task": task.name,
                "passed": passed,
                "result": str(result)[:100],
                "expected": str(task.expected)[:50],
                "difficulty": task.difficulty,
            })

            if verbose:
                status = "✅" if passed else "❌"
                print(f"{status} {task.name} ({task.difficulty})")

        except Exception as e:
            results.append({
                "task": task.name,
                "passed": False,
                "error": str(e),
                "difficulty": task.difficulty,
            })
            if verbose:
                print(f"❌ {task.name}: {e}")

    return {
        "total": len(results),
        "passed": sum(1 for r in results if r.get("passed")),
        "results": results,
    }


def _execute_task(mm, task) -> str:
    """Execute a single memory task and return result string."""
    from core.memory.stores import InMemoryStore

    if task.name == "memory_preference_set":
        mm.get_store("preference").set_preference("name", "Alice")
        return "ok"
    elif task.name == "memory_preference_get":
        val = mm.get_store("preference").get_preference("name", "")
        return str(val) if val else ""
    elif task.name == "memory_preference_list":
        prefs = mm.get_store("preference").get_all_preferences()
        return json.dumps(prefs)
    elif task.name == "memory_long_term_store":
        mm.get_store("long_term").set("core_modules", "agent, tools, llm")
        return "ok"
    elif task.name == "memory_long_term_recall":
        val = mm.get_store("long_term").get("core_modules", "")
        return str(val) if val else ""
    elif task.name == "memory_forget":
        mm.get_store("long_term").delete("name")
        return "ok"
    elif task.name == "memory_working_store":
        mm.get_store("working").set("progress", "完成了第一步")
        return "ok"
    elif task.name == "memory_working_recall":
        val = mm.get_store("working").get("progress", "")
        return str(val) if val else ""
    elif task.name == "memory_cross_session_recall":
        cross = mm.get_store("cross_session")
        if hasattr(cross, "save_summarized_context"):
            cross.save_summarized_context("test_session_1", "完成了nanoagent项目分析")
        ctx = cross.get_recent_context(1) if hasattr(cross, "get_recent_context") else []
        return json.dumps(ctx)
    elif task.name == "memory_search":
        cross = mm.get_store("cross_session")
        if hasattr(cross, "find_related_context"):
            results_search = cross.find_related_context("nanoagent", limit=3)
            return json.dumps(results_search)
        else:
            return "[]"
    elif task.name == "memory_status":
        stores = {}
        for name in ["short_term", "working", "long_term", "cross_session", "preference"]:
            store = mm.get_store(name)
            if store:
                stores[name] = store.memory_type
        return json.dumps({"status": "ok", "stores": stores})
    elif task.name == "memory_token_budget":
        ctx = mm.build_context_for_prompt(max_tokens=500)
        return f"context_length={len(ctx)}"
    elif task.name == "memory_hot_swap":
        original = mm.get_store("long_term")
        mm.register_store("long_term", InMemoryStore())
        mm.get_store("long_term").set("test", "value")
        retrieved = mm.get_store("long_term").get("test")
        mm.register_store("long_term", original)
        return "ok" if retrieved == "value" else "fail"
    else:
        return "unknown_task"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run memory eval")
    parser.add_argument("--mock", action="store_true", help="Use mock mode")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--reset", action="store_true", help="Reset memory before test")
    args = parser.parse_args()

    if args.reset:
        from core.memory import reset_memory_manager
        reset_memory_manager()
        print("Memory reset.")

    result = run_memory_eval(mock=args.mock, verbose=args.verbose)

    print("\n" + "=" * 60)
    print(f"  准确率: {result['passed']}/{result['total']} ({100*result['passed']/max(result['total'],1):.1f}%)")
    print("=" * 60)

    for r in result["results"]:
        status = "✅" if r.get("passed") else "❌"
        print(f"  {status} {r['task']}")

    sys.exit(0 if result["passed"] == result["total"] else 1)