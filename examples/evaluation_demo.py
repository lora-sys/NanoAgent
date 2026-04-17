"""评估功能演示 - 展示如何使用 nanoagent 的评估系统

这个示例展示了评估框架的主要功能：
1. 创建自定义评估任务
2. 运行评估套件
3. 分析评估结果
4. 生成评估报告
"""

from core.agent import NanoAgent
from core.evaluation import (
    EvaluationTask,
    EvaluationRunner,
    EvaluationAnalyzer,
    TaskDifficulty,
    VerificationType,
)


def demo_basic_evaluation():
    """演示基础评估功能"""
    print("🎯 基础评估演示")
    print("=" * 80)

    # 创建代理
    agent = NanoAgent()

    # 创建简单的评估任务
    task = EvaluationTask(
        name="demo_file_reading",
        description="演示文件读取评估",
        prompt="读取 README.md 文件并总结前3行内容",
        difficulty=TaskDifficulty.BASIC,
        verification_type=VerificationType.CONTAINS,
        expected_result=["README", "总结"],
        expected_tools=["read_file"],
    )

    # 运行评估
    runner = EvaluationRunner(agent)
    result = runner.run_task(task)

    print("\n✅ 评估完成")
    print(f"结果: {result['verification']['passed']}")

    return result


def demo_custom_tasks():
    """演示自定义评估任务"""
    print("\n🎯 自定义评估任务演示")
    print("=" * 80)

    # 创建代理
    agent = NanoAgent()

    # 创建多个自定义任务
    custom_tasks = [
        EvaluationTask(
            name="custom_dir_list",
            description="自定义目录列表任务",
            prompt="列出 core/ 目录的所有 Python 文件",
            difficulty=TaskDifficulty.BASIC,
            verification_type=VerificationType.CONTAINS,
            expected_result=["core", "Python"],
            expected_tools=["list_files"],
        ),
        EvaluationTask(
            name="custom_command",
            description="自定义命令执行任务",
            prompt="运行 'pwd' 命令并解释输出",
            difficulty=TaskDifficulty.BASIC,
            verification_type=VerificationType.CONTAINS,
            expected_result=["目录", "pwd"],
            expected_tools=["run_bash"],
        ),
    ]

    # 运行评估套件
    runner = EvaluationRunner(agent)
    results = runner.run_evaluation_suite(custom_tasks)

    print("\n✅ 套件评估完成")
    print(f"成功率: {results['summary']['success_rate']:.1%}")

    return results


def demo_evaluation_analysis():
    """演示评估结果分析"""
    print("\n🎯 评估结果分析演示")
    print("=" * 80)

    # 创建代理
    agent = NanoAgent()

    # 创建测试任务
    test_tasks = [
        EvaluationTask(
            name="analysis_task_1",
            description="分析任务1",
            prompt="读取 config.py 文件",
            difficulty=TaskDifficulty.BASIC,
            verification_type=VerificationType.CONTAINS,
            expected_result=["config"],
            expected_tools=["read_file"],
        ),
        EvaluationTask(
            name="analysis_task_2",
            description="分析任务2",
            prompt="列出 tests/ 目录",
            difficulty=TaskDifficulty.BASIC,
            verification_type=VerificationType.CONTAINS,
            expected_result=["tests"],
            expected_tools=["list_files"],
        ),
    ]

    # 运行评估
    runner = EvaluationRunner(agent)
    results = runner.run_evaluation_suite(test_tasks)

    # 分析结果
    analysis = EvaluationAnalyzer.analyze_results(results)

    # 显示分析结果
    print("\n📊 性能分析:")
    perf = analysis["performance_analysis"]
    print(f"  平均执行时间: {perf['average_execution_time']:.2f}秒")
    print(f"  平均迭代次数: {perf['average_iterations']:.1f}次")

    print("\n🔧 工具使用分析:")
    tool_usage = analysis["tool_usage_analysis"]
    for tool, stats in tool_usage["tool_statistics"].items():
        print(f"  {tool}: 使用{stats['used']}次")

    print("\n💡 改进建议:")
    for suggestion in analysis["improvement_suggestions"]:
        print(f"  - {suggestion}")

    return analysis


def demo_difficulty_levels():
    """演示不同难度级别的评估"""
    print("\n🎯 难度级别演示")
    print("=" * 80)

    # 创建代理
    agent = NanoAgent()

    # 创建不同难度的任务
    tasks_by_difficulty = {
        "basic": EvaluationTask(
            name="basic_demo",
            description="基础难度任务",
            prompt="读取 README.md 文件",
            difficulty=TaskDifficulty.BASIC,
            verification_type=VerificationType.CONTAINS,
            expected_result=["README"],
            expected_tools=["read_file"],
        ),
        "intermediate": EvaluationTask(
            name="intermediate_demo",
            description="中等难度任务",
            prompt="分析 core/ 目录的结构，列出所有模块文件",
            difficulty=TaskDifficulty.INTERMEDIATE,
            verification_type=VerificationType.CONTAINS,
            expected_result=["core", "模块"],
            expected_tools=["list_files", "read_file"],
        ),
    }

    # 分别运行不同难度的任务
    runner = EvaluationRunner(agent)

    for level, task in tasks_by_difficulty.items():
        print(f"\n📊 运行 {level.upper()} 任务...")
        result = runner.run_task(task)
        print(
            f"✅ {level.upper()} 任务完成: {'通过' if result['verification']['passed'] else '失败'}"
        )

    return tasks_by_difficulty


def demo_verification_types():
    """演示不同的验证类型"""
    print("\n🎯 验证类型演示")
    print("=" * 80)

    # 创建代理
    agent = NanoAgent()

    # 创建不同验证类型的任务
    verification_tasks = [
        EvaluationTask(
            name="contains_verify",
            description="包含匹配验证",
            prompt="读取 README.md 文件",
            difficulty=TaskDifficulty.BASIC,
            verification_type=VerificationType.CONTAINS,
            expected_result=["NanoAgent"],
            expected_tools=["read_file"],
        ),
        EvaluationTask(
            name="tool_calls_verify",
            description="工具调用验证",
            prompt="列出 examples/ 目录然后读取一个文件",
            difficulty=TaskDifficulty.INTERMEDIATE,
            verification_type=VerificationType.TOOL_CALLS,
            expected_result="",  # 不检查内容，只检查工具调用
            expected_tools=["list_files", "read_file"],
        ),
    ]

    # 运行评估
    runner = EvaluationRunner(agent)
    results = runner.run_evaluation_suite(verification_tasks)

    print("\n✅ 验证类型演示完成")

    return results


def demo_real_world_scenario():
    """演示真实世界评估场景"""
    print("\n🎯 真实世界评估场景演示")
    print("=" * 80)

    # 创建代理
    agent = NanoAgent()

    # 模拟真实世界的评估场景
    real_world_tasks = [
        EvaluationTask(
            name="project_onboarding",
            description="新成员项目入门",
            prompt="帮助新开发者了解项目：1) 读取 README.md，2) 查看项目结构，3) 总结核心功能",
            difficulty=TaskDifficulty.INTERMEDIATE,
            verification_type=VerificationType.CONTAINS,
            expected_result=["项目", "功能", "结构"],
            expected_tools=["read_file", "list_files"],
            metadata={"real_world_scenario": "新成员入职培训", "importance": "high"},
        ),
        EvaluationTask(
            name="code_review_assistant",
            description="代码审查助手",
            prompt="审查 core/agent.py 的代码质量，检查错误处理和工具调用逻辑",
            difficulty=TaskDifficulty.ADVANCED,
            verification_type=VerificationType.CONTAINS,
            expected_result=["代码", "质量", "错误"],
            expected_tools=["read_file"],
            metadata={"real_world_scenario": "代码质量保证", "importance": "high"},
        ),
    ]

    # 运行真实世界评估
    runner = EvaluationRunner(agent)
    results = runner.run_evaluation_suite(real_world_tasks)

    # 分析结果
    analysis = EvaluationAnalyzer.analyze_results(results)

    print("\n📊 真实世界场景评估结果:")
    print(f"  成功率: {results['summary']['success_rate']:.1%}")
    print(
        f"  平均执行时间: {analysis['performance_analysis']['average_execution_time']:.2f}秒"
    )

    return results


def main():
    """主函数 - 运行精选演示"""
    print("🚀 NanoAgent 评估系统演示")
    print("=" * 80)
    print()

    try:
        # 只运行最核心的演示
        print("📋 运行核心评估演示...")
        print()

        # 1. 基础评估演示（最简单的）
        print("【1/2】基础评估演示")
        demo_basic_evaluation()

        # 2. 评估分析演示（展示分析能力）
        print("\n【2/2】评估分析演示")
        demo_evaluation_analysis()

        print("\n" + "=" * 80)
        print("🎉 核心演示完成！")
        print("💡 提示：运行 'python tests/run_evaluation.py --basic' 查看更多评估")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
