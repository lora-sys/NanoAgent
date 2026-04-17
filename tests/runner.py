"""测试运行器 - 简洁直接的测试执行

设计原则：
- 工具调用验证为核心
- 关键词验证为参考（真实 API 模式）
- Mock 模式宽松，真实模式严格

使用方式:
    PYTHONPATH=. uv run python tests/runner.py              # 运行所有测试（真实 API）
    PYTHONPATH=. uv run python tests/runner.py --mock     # mock 模式测试
    PYTHONPATH=. uv run python tests/runner.py --category file  # 按类别
    PYTHONPATH=. uv run python tests/runner.py --list     # 列出测试
"""

import sys
import json

from core.agent import NanoAgent
from tests.prompts import get_tests_by_category, TestCase


def run_test(agent: NanoAgent, test: TestCase, strict: bool = True) -> dict:
    """运行单个测试

    Args:
        agent: NanoAgent 实例
        test: 测试用例
        strict: 严格模式（验证关键词），宽松模式只验证工具
    """
    print(f"\n{'─' * 50}")
    print(f"测试: {test.name}")
    print(f"提示: {test.prompt}")
    print(f"预期工具: {test.expected_tools}")
    print("─" * 50)

    try:
        result = agent.run(test.prompt, max_iterations=15)

        response = result.get("response", "")
        tools_used = result.get("tools_used", [])
        status = result.get("status", "unknown")

        # 验证工具使用 - 必须有交集
        tools_found = [t for t in test.expected_tools if t in tools_used]
        tools_ok = len(tools_found) > 0

        # 检查parse错误
        has_parse_error = "__parse_error__" in tools_used

        # 关键词验证（严格模式）
        keywords_found = [kw for kw in test.expected_keywords if kw in response]
        kw_ratio = (
            len(keywords_found) / len(test.expected_keywords)
            if test.expected_keywords
            else 0
        )
        keywords_ok = kw_ratio >= 0.5 if strict else True

        # 最终结果
        # 严格模式: 完成 + 工具 + 关键词
        # 宽松模式: 完成 + 工具 + 无解析错误
        passed = (
            status == "completed" and tools_ok and keywords_ok and not has_parse_error
        )

        # 输出
        print(f"状态: {status}")
        print(f"工具: {tools_used} {'✓' if tools_ok else '✗'}")
        if strict:
            print(
                f"关键词: {keywords_found}/{test.expected_keywords} ({kw_ratio * 100:.0f}%)"
            )
        print(f"结果: {'✓ PASS' if passed else '✗ FAIL'}")

        return {
            "name": test.name,
            "passed": passed,
            "status": status,
            "tools_expected": test.expected_tools,
            "tools_used": tools_used,
            "tools_found": tools_found,
            "keywords_found": keywords_found,
            "kw_ratio": kw_ratio,
            "strict": strict,
        }

    except Exception as e:
        print(f"错误: {e}")
        return {
            "name": test.name,
            "passed": False,
            "error": str(e),
        }


def run_all_tests(agent: NanoAgent, category: str = "all", strict: bool = True) -> dict:
    """运行测试套件"""
    tests = get_tests_by_category(category)
    if not tests:
        print(f"未知类别: {category}")
        return {"total": 0, "passed": 0, "failed": 0}

    print(f"\n{'=' * 60}")
    print(f"NanoAgent 测试 - {category.upper()}")
    print(f"{'=' * 60}")
    print(f"测试数: {len(tests)}")
    print(f"模式: {'严格' if strict else '宽松'}")

    results = []
    for test in tests:
        result = run_test(agent, test, strict)
        results.append(result)

    # 汇总
    total = len(results)
    passed = sum(1 for r in results if r.get("passed", False))
    failed = total - passed

    print(f"\n{'=' * 60}")
    print("测试汇总")
    print("=" * 60)
    print(f"总计: {total}")
    print(f"通过: {passed} ✓")
    print(f"失败: {failed} ✗")
    print(f"成功率: {passed / total * 100:.1f}%")

    # 失败详情
    if failed > 0:
        print("\n失败详情:")
        for r in results:
            if not r.get("passed"):
                reasons = []
                if r.get("status") != "completed":
                    reasons.append(f"状态={r.get('status')}")
                if len(r.get("tools_found", [])) == 0:
                    reasons.append("工具不匹配")
                if r.get("kw_ratio", 0) < 0.5 and strict:
                    reasons.append(f"关键词({r.get('kw_ratio', 0) * 100:.0f}%)")
                if "__parse_error__" in r.get("tools_used", []):
                    reasons.append("解析错误")
                if "error" in r:
                    reasons.append(f"错误:{r['error'][:50]}")
                print(f"  ✗ {r['name']}: {', '.join(reasons)}")

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "success_rate": passed / total if total > 0 else 0,
        "category": category,
        "strict": strict,
        "results": results,
    }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="NanoAgent 测试运行器")
    parser.add_argument(
        "--category",
        "-c",
        default="all",
        help="测试类别: file, directory, command, composite, error, all",
    )
    parser.add_argument("--list", "-l", action="store_true", help="列出所有测试")
    parser.add_argument("--output", "-o", type=str, help="输出结果到JSON文件")
    parser.add_argument(
        "--mock", "-m", action="store_true", help="宽松模式（只验证工具，不验证关键词）"
    )

    args = parser.parse_args()

    if args.list:
        from tests.prompts import print_test_summary

        print_test_summary()
        return 0

    # 宽松模式默认用于 mock 测试
    strict = not args.mock

    agent = NanoAgent()
    results = run_all_tests(agent, args.category, strict)

    # 保存结果
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n结果已保存: {args.output}")

    # 返回码
    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
