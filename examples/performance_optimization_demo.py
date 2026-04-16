"""性能优化演示 - 展示如何使用性能优化器和语义验证器

这个示例展示了：
1. 性能优化器的使用
2. 语义验证器的使用
3. 工具响应压缩
4. 基于评估结果的优化建议
"""

from core.agent import NanoAgent
from core.performance_optimizer import (
    create_performance_optimizer,
    create_response_compressor,
)
from core.semantic_verifier import SemanticMatchType, create_semantic_verifier


def demo_performance_optimizer():
    """演示性能优化器"""
    print("🎯 性能优化器演示")
    print("=" * 80)

    # 创建优化器
    optimizer = create_performance_optimizer()

    # 模拟工具调用数据
    print("\n📊 记录工具调用数据...")

    # 模拟一些工具调用
    optimizer.record_tool_call(
        "read_file", execution_time=2.5, success=True, expected=True
    )
    optimizer.record_tool_call(
        "read_file", execution_time=3.0, success=True, expected=True
    )
    optimizer.record_tool_call(
        "read_file", execution_time=1.8, success=True, expected=False
    )  # 不必要的调用
    optimizer.record_tool_call(
        "list_files", execution_time=1.2, success=True, expected=True
    )
    optimizer.record_tool_call(
        "list_files", execution_time=1.5, success=True, expected=True
    )
    optimizer.record_tool_call(
        "run_bash", execution_time=0.8, success=True, expected=True
    )
    optimizer.record_tool_call(
        "run_bash", execution_time=1.2, success=False, expected=True
    )

    print("✅ 记录了 7 次工具调用")

    # 分析性能
    print("\n🔍 分析性能...")
    suggestions = optimizer.analyze_performance()

    print(f"\n📋 发现 {len(suggestions)} 个优化建议:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. {suggestion.tool_name} - {suggestion.issue_type}")
        print(f"   严重程度: {suggestion.severity}")
        print(f"   描述: {suggestion.description}")
        print(f"   建议: {suggestion.suggestion}")
        print(f"   预期改进: {suggestion.expected_improvement}")

    # 获取性能报告
    print("\n📊 性能报告:")
    report = optimizer.get_performance_report()

    print(f"   总调用次数: {report['summary']['total_calls']}")
    print(f"   总成功次数: {report['summary']['total_success']}")
    print(f"   整体成功率: {report['summary']['overall_success_rate']:.1%}")
    print(f"   分析的工具数: {report['summary']['tools_analyzed']}")

    print("\n   各工具指标:")
    for tool_name, metrics in report["tool_metrics"].items():
        print(f"     {tool_name}:")
        print(f"       调用次数: {metrics['call_count']}")
        print(f"       成功率: {metrics['success_rate']:.1%}")
        print(f"       平均执行时间: {metrics['avg_execution_time']:.2f}秒")
        print(f"       效率分数: {metrics['efficiency_score']:.2f}")

    return optimizer


def demo_response_compressor():
    """演示响应压缩器"""
    print("\n🎯 响应压缩器演示")
    print("=" * 80)

    compressor = create_response_compressor()

    # 演示文件列表压缩
    print("\n📁 压缩文件列表:")
    large_file_list = [
        {"filename": "file1.py", "type": "file"},
        {"filename": "file2.py", "type": "file"},
        {"filename": "file3.py", "type": "file"},
        {"filename": "dir1", "type": "dir"},
        {"filename": "dir2", "type": "dir"},
    ] * 10  # 模拟大量文件

    print(f"   原始文件数: {len(large_file_list)}")

    compressed = compressor.compress_file_list(large_file_list)
    print("   压缩后:")
    print(f"     显示文件数: {len(compressed['files'])}")
    print(f"     显示目录数: {len(compressed['dirs'])}")
    print(f"     总文件数: {compressed['total_files']}")
    print(f"     总目录数: {compressed['total_dirs']}")

    # 演示文件内容压缩
    print("\n📄 压缩文件内容:")
    long_content = "这是一段很长的文件内容。" * 100  # 模拟长文件
    print(f"   原始长度: {len(long_content)} 字符")

    compressed_content = compressor.compress_file_content(long_content, max_length=200)
    print(f"   压缩后长度: {len(compressed_content)} 字符")
    print(f"   压缩后内容: {compressed_content[:100]}...")

    # 估算 token 节省
    savings = compressor.estimate_token_savings(large_file_list, compressed)
    print("\n💰 Token 节省估算:")
    print(f"   原始 tokens: {savings['original_tokens']}")
    print(f"   压缩 tokens: {savings['compressed_tokens']}")
    print(f"   节省 tokens: {savings['saved_tokens']}")
    print(f"   节省比例: {savings['savings_percentage']:.1f}%")

    return compressor


def demo_semantic_verifier():
    """演示语义验证器"""
    print("\n🎯 语义验证器演示")
    print("=" * 80)

    verifier = create_semantic_verifier()

    # 测试不同的匹配类型
    test_cases = [
        {
            "name": "精确匹配",
            "expected": "Hello World",
            "actual": "Hello World",
            "match_type": SemanticMatchType.EXACT,
        },
        {
            "name": "包含匹配",
            "expected": ["Python", "编程"],
            "actual": "这是一个Python编程示例",
            "match_type": SemanticMatchType.CONTAINS,
        },
        {
            "name": "语义相似",
            "expected": "读取README文件并总结内容",
            "actual": "我已经读取了README.md文件，主要内容是关于项目介绍和快速开始方法",
            "match_type": SemanticMatchType.SEMANTIC_SIMILAR,
        },
        {
            "name": "关键词匹配",
            "expected": "分析项目结构",
            "actual": "项目的核心模块包括agent.py, router.py, chain.py等文件",
            "match_type": SemanticMatchType.KEYWORD_BASED,
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   预期: {test_case['expected']}")
        print(f"   实际: {test_case['actual']}")

        result = verifier.verify_semantic_match(
            expected=test_case["expected"],
            actual=test_case["actual"],
            match_type=test_case["match_type"],
        )

        print(f"   匹配类型: {result.match_type.value}")
        print(f"   置信度: {result.confidence:.2f}")
        print(f"   是否匹配: {'✅ 是' if result.is_match() else '❌ 否'}")

        if result.matched_elements:
            print(f"   匹配元素: {result.matched_elements[:3]}...")
        if result.missing_elements:
            print(f"   缺失元素: {result.missing_elements[:3]}...")

    # 测试工具调用序列验证
    print("\n🔧 工具调用序列验证:")
    expected_tools = ["read_file", "list_files", "run_bash"]
    actual_tools = ["list_files", "read_file", "run_bash"]

    sequence_result = verifier.verify_tool_call_sequence(expected_tools, actual_tools)
    print(f"   预期序列: {expected_tools}")
    print(f"   实际序列: {actual_tools}")
    print(f"   置信度: {sequence_result.confidence:.2f}")
    print(f"   是否匹配: {'✅ 是' if sequence_result.is_match() else '❌ 否'}")

    return verifier


def demo_integrated_optimization():
    """演示集成的性能优化"""
    print("\n🎯 集成性能优化演示")
    print("=" * 80)

    # 创建代理和优化器
    agent = NanoAgent()
    optimizer = create_performance_optimizer()
    compressor = create_response_compressor()

    print("\n🤖 运行优化任务...")

    # 模拟一个任务
    task = "读取 README.md 文件"
    print(f"   任务: {task}")

    # 记录工具调用
    print("\n📊 记录工具调用:")
    optimizer.record_tool_call(
        "read_file", execution_time=2.3, success=True, expected=True
    )
    print("   ✅ read_file - 2.3秒 - 成功")

    # 模拟响应压缩
    print("\n🗜️ 响应压缩:")
    original_response = {
        "file_path": "/home/lora/repos/nanoagent/README.md",
        "content": "# NanoAgent\n\n极简 Agent 框架 - 零魔法，高性能\n\n## 特性\n\n- **极简设计**：核心逻辑不到 200 行代码\n- **零魔法**：纯 Python 内置函数，无复杂依赖\n- **高性能**：使用 Python 内置函数，最小化开销\n- **易扩展**：简单的工具注册机制\n- **灵活控制**：无步数限制，自定义停止条件",
    }

    compressed_response = optimizer.optimize_tool_response(
        "read_file", original_response
    )
    print(f"   原始响应大小: {len(str(original_response))} 字符")
    print(f"   压缩响应大小: {len(str(compressed_response))} 字符")

    # 生成优化建议
    print("\n💡 优化建议:")
    suggestions = optimizer.analyze_performance()
    if suggestions:
        for suggestion in suggestions:
            print(f"   - {suggestion.suggestion}")
    else:
        print("   ✅ 当前性能良好，无需优化")

    return agent, optimizer, compressor


def main():
    """主函数 - 运行所有演示"""
    print("🚀 NanoAgent 性能优化系统演示")
    print("=" * 80)
    print()

    try:
        # 1. 性能优化器演示
        demo_performance_optimizer()

        # 2. 响应压缩器演示
        demo_response_compressor()

        # 3. 语义验证器演示
        demo_semantic_verifier()

        # 4. 集成优化演示
        demo_integrated_optimization()

        print("\n" + "=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n💡 提示:")
        print("   - 运行 'python tests/run_evaluation.py' 查看完整的性能分析")
        print("   - 查看性能报告以获取详细的优化建议")
        print("   - 使用语义验证器提高验证准确性")

    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
