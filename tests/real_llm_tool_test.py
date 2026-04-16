"""真实 LLM 工具使用测试 - 测试模型如何使用工具"""

import asyncio
from core.agent import NanoAgent


async def test_tool_usage():
    """测试工具使用"""
    print("🚀 真实 LLM 工具使用测试")
    print("=" * 80)
    print()

    agent = NanoAgent()

    # 测试提示词 - 覆盖各种工具使用场景
    test_prompts = [
        # 基础工具使用
        {
            "name": "基础文件操作",
            "prompt": "读取 README.md 文件的内容",
            "expected_tools": ["read_file"],
            "focus": "基础工具使用",
        },
        # 复杂任务分解
        {
            "name": "项目分析",
            "prompt": "分析当前项目的目录结构，找出主要的 Python 文件",
            "expected_tools": ["list_files", "read_file"],
            "focus": "工具组合使用",
        },
        # 边界情况 - 空目录
        {
            "name": "空目录检查",
            "prompt": "检查 /tmp/empty 目录是否存在并列出文件",
            "expected_tools": ["list_files"],
            "focus": "边界情况处理",
        },
        # 容易出错的情况 - 文件编辑
        {
            "name": "文件编辑",
            "prompt": "在 README.md 文件末尾添加一行 '测试添加内容'",
            "expected_tools": ["read_file", "edit_file"],
            "focus": "文件编辑准确性",
        },
        # 复杂的多步任务
        {
            "name": "代码搜索",
            "prompt": "搜索项目中所有包含 'def main' 的 Python 文件",
            "expected_tools": ["list_files", "read_file"],
            "focus": "多步任务执行",
        },
        # 命令执行
        {
            "name": "系统命令",
            "prompt": "运行命令 'python --version' 检查 Python 版本",
            "expected_tools": ["run_bash"],
            "focus": "命令执行安全性",
        },
        # 工具选择测试
        {
            "name": "工具选择",
            "prompt": "列出当前目录的所有文件，然后读取第一个 .py 文件",
            "expected_tools": ["list_files", "read_file"],
            "focus": "工具选择准确性",
        },
        # 错误恢复
        {
            "name": "错误恢复",
            "prompt": "尝试读取不存在的文件 /nonexistent/file.txt",
            "expected_tools": ["read_file"],
            "focus": "错误处理能力",
        },
        # 上下文理解
        {
            "name": "上下文理解",
            "prompt": "先列出 core/ 目录的文件，然后读取 agent.py 文件，最后分析它的主要功能",
            "expected_tools": ["list_files", "read_file"],
            "focus": "上下文保持",
        },
        # 工具参数准确性
        {
            "name": "参数准确性",
            "prompt": "使用 list_files 工具列出 examples/ 目录的内容",
            "expected_tools": ["list_files"],
            "focus": "参数传递准确性",
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

            if not tool_match:
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

    # 改进建议
    print("💡 改进建议:")
    print()

    suggestions = []

    # 检查工具定义是否清晰
    if any(
        "参数准确性" in r.get("focus", "") and not r.get("tool_match", False)
        for r in results
    ):
        suggestions.append("1. 改进工具参数描述，使其更加明确和具体")

    # 检查边界情况处理
    if any(
        "边界情况" in r.get("focus", "") and not r.get("tool_match", False)
        for r in results
    ):
        suggestions.append("2. 增强边界情况的错误处理和提示")

    # 检查多步任务
    if any(
        "多步任务" in r.get("focus", "") and not r.get("tool_match", False)
        for r in results
    ):
        suggestions.append("3. 改进多步任务的执行逻辑和上下文保持")

    # 检查工具选择
    if any(
        "工具选择" in r.get("focus", "") and not r.get("tool_match", False)
        for r in results
    ):
        suggestions.append("4. 优化工具选择逻辑，提高准确性")

    # 检查错误恢复
    if any(
        "错误恢复" in r.get("focus", "") and not r.get("tool_match", False)
        for r in results
    ):
        suggestions.append("5. 加强错误恢复能力，提供更友好的错误信息")

    if suggestions:
        for suggestion in suggestions:
            print(f"  {suggestion}")
    else:
        print("  ✅ 当前工具设计良好，无需重大改进")

    print()
    print("=" * 80)
    print("🎉 测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_tool_usage())
