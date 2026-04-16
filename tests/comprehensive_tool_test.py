"""全面的工具使用测试"""

import asyncio
from core.agent import NanoAgent


async def test_comprehensive_tools():
    """全面的工具使用测试"""
    print("🚀 全面工具使用测试")
    print("=" * 80)
    print()

    agent = NanoAgent()

    # 测试提示词
    test_prompts = [
        {
            "name": "文件读取",
            "prompt": "读取 README.md 文件的前 5 行",
            "expected_tools": ["read_file"],
            "focus": "文件操作",
        },
        {
            "name": "目录列表",
            "prompt": "列出 examples/ 目录的所有文件",
            "expected_tools": ["list_files"],
            "focus": "目录操作",
        },
        {
            "name": "命令执行",
            "prompt": "运行命令 'pwd' 显示当前目录",
            "expected_tools": ["run_bash"],
            "focus": "命令执行",
        },
        {
            "name": "组合任务",
            "prompt": "先列出 core/ 目录的文件，然后读取 agent.py 文件的内容",
            "expected_tools": ["list_files", "read_file"],
            "focus": "工具组合",
        },
        {
            "name": "复杂查询",
            "prompt": "查找项目中所有包含 'def' 的 Python 文件",
            "expected_tools": ["list_files", "read_file"],
            "focus": "多步任务",
        },
    ]

    results = []

    for i, test_case in enumerate(test_prompts, 1):
        print(f"🎯 测试 {i}/{len(test_prompts)}: {test_case['name']}")
        print(f"📋 提示词: {test_case['prompt']}")
        print(f"🎯 关注点: {test_case['focus']}")
        print()

        try:
            # 执行任务
            result = agent.run(test_case["prompt"], max_iterations=5)

            # 分析结果
            used_tools = result.get("tools_used", [])
            status = result.get("status", "unknown")
            iterations = result.get("iterations", 0)

            # 检查是否使用了预期的工具
            expected_tools = test_case["expected_tools"]
            tool_match = any(tool in used_tools for tool in expected_tools)

            test_result = {
                "name": test_case["name"],
                "prompt": test_case["prompt"],
                "used_tools": used_tools,
                "expected_tools": expected_tools,
                "tool_match": tool_match,
                "status": status,
                "iterations": iterations,
                "focus": test_case["focus"],
            }

            results.append(test_result)

            # 输出结果
            print(f"✅ 状态: {status}")
            print(f"🔧 使用的工具: {used_tools}")
            print(f"🎯 预期工具: {expected_tools}")
            print(f"📊 工具匹配: {'✅' if tool_match else '❌'}")
            print(f"🔄 迭代次数: {iterations}")

            if tool_match:
                print("✅ 工具使用正常")
            else:
                print("⚠️ 警告: 模型没有使用预期的工具")

            print()
            print("-" * 80)
            print()

        except Exception as e:
            print(f"❌ 错误: {e}")
            print()
            print("-" * 80)
            print()

            results.append(
                {
                    "name": test_case["name"],
                    "prompt": test_case["prompt"],
                    "error": str(e),
                    "status": "failed",
                    "expected_tools": test_case["expected_tools"],
                    "used_tools": [],
                    "tool_match": False,
                }
            )

    # 生成测试报告
    print("=" * 80)
    print("📊 测试报告")
    print("=" * 80)
    print()

    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.get("tool_match", False))
    failed_tests = total_tests - passed_tests

    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests} ({passed_tests / total_tests * 100:.1f}%)")
    print(f"失败: {failed_tests} ({failed_tests / total_tests * 100:.1f}%)")
    print()

    # 按关注点分析
    print("🎯 按关注点分析:")
    print()
    focus_areas = {}
    for result in results:
        focus = result.get("focus", "unknown")
        if focus not in focus_areas:
            focus_areas[focus] = {"total": 0, "passed": 0}
        focus_areas[focus]["total"] += 1
        if result.get("tool_match", False):
            focus_areas[focus]["passed"] += 1

    for focus, stats in focus_areas.items():
        pass_rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {focus}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")

    print()

    # 识别问题
    print("🔍 识别的问题:")
    print()

    problems = []
    for result in results:
        if not result.get("tool_match", False):
            problems.append(
                {
                    "name": result["name"],
                    "prompt": result["prompt"],
                    "expected": result["expected_tools"],
                    "actual": result.get("used_tools", []),
                    "focus": result.get("focus", "unknown"),
                }
            )

    if problems:
        for problem in problems:
            print(f"  ❌ {problem['name']}")
            print(f"     提示词: {problem['prompt']}")
            print(f"     预期工具: {problem['expected']}")
            print(f"     实际工具: {problem['actual']}")
            print(f"     关注点: {problem['focus']}")
            print()
    else:
        print("  ✅ 没有发现明显问题")
        print()

    print("=" * 80)
    print("🎉 测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_comprehensive_tools())
