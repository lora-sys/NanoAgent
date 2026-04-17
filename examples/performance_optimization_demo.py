"""性能优化演示 - 简化版本

展示如何使用简化的性能优化器和语义验证器
"""

from core.performance_optimizer import create_optimizer, create_compressor
from core.semantic_verifier import create_verifier, MatchType


def demo_optimizer():
    """演示优化器"""
    print("🎯 性能优化器")
    print("=" * 80)

    optimizer = create_optimizer()

    # 记录一些调用
    print("\n📊 记录工具调用:")
    optimizer.record_call("read_file", 2.5, True, True)
    optimizer.record_call("read_file", 3.0, True, True)
    optimizer.record_call("read_file", 1.8, True, False)  # 不必要
    optimizer.record_call("list_files", 1.2, True, True)
    optimizer.record_call("run_bash", 0.8, True, True)
    optimizer.record_call("run_bash", 1.2, False, True)

    # 获取统计
    print("\n📈 性能统计:")
    stats = optimizer.get_stats()
    for tool, data in stats.items():
        print(f"  {tool}:")
        print(f"    调用: {data['calls']}")
        print(f"    成功率: {data['success_rate']:.0%}")
        print(f"    平均时间: {data['avg_time']:.2f}s")
        print(f"    不必要率: {data['unnecessary_rate']:.0%}")

    # 获取建议
    print("\n💡 优化建议:")
    suggestions = optimizer.get_suggestions()
    for suggestion in suggestions:
        print(f"  - {suggestion}")


def demo_compressor():
    """演示压缩器"""
    print("\n🎯 响应压缩器")
    print("=" * 80)

    compressor = create_compressor()

    # 压缩文件列表
    print("\n📁 压缩文件列表:")
    files = [{"filename": f"file{i}.py", "type": "file"} for i in range(30)] + [
        {"filename": f"dir{i}", "type": "dir"} for i in range(15)
    ]

    print(f"  原始: {len(files)} 项")
    compressed = compressor.compress_file_list(files)
    print(f"  压缩: {len(compressed['files'])} 文件 + {len(compressed['dirs'])} 目录")
    print(f"  总计: {compressed['total_files']} 文件, {compressed['total_dirs']} 目录")

    # 压缩内容
    print("\n📄 压缩内容:")
    long_content = "这是一段很长的内容。" * 100
    print(f"  原始: {len(long_content)} 字符")
    compressed_content = compressor.compress_content(long_content, 200)
    print(f"  压缩: {len(compressed_content)} 字符")
    print(f"  预览: {compressed_content[:80]}...")


def demo_verifier():
    """演示验证器"""
    print("\n🎯 语义验证器")
    print("=" * 80)

    verifier = create_verifier()

    # 测试不同匹配类型
    tests = [
        ("精确匹配", "Hello World", "Hello World", MatchType.EXACT),
        ("包含匹配", ["Python", "编程"], "这是一个Python编程示例", MatchType.CONTAINS),
        ("语义匹配", "读取README文件", "我已经读取了README.md文件", MatchType.SEMANTIC),
    ]

    for name, expected, actual, match_type in tests:
        print(f"\n{name}:")
        print(f"  预期: {expected}")
        print(f"  实际: {actual}")

        result = verifier.verify(expected, actual, match_type)
        print(f"  匹配: {'✅' if result.matched else '❌'}")
        print(f"  置信度: {result.confidence:.2f}")
        print(f"  详情: {result.details}")

    # 工具序列验证
    print("\n工具序列验证:")
    expected_tools = ["read_file", "list_files"]
    actual_tools = ["list_files", "read_file"]

    result = verifier.verify_tool_sequence(expected_tools, actual_tools)
    print(f"  预期: {expected_tools}")
    print(f"  实际: {actual_tools}")
    print(f"  匹配: {'✅' if result.matched else '❌'}")
    print(f"  置信度: {result.confidence:.2f}")


def main():
    """主函数"""
    print("🚀 NanoAgent 简化版性能优化演示")
    print("=" * 80)
    print()

    try:
        demo_optimizer()
        demo_compressor()
        demo_verifier()

        print("\n" + "=" * 80)
        print("🎉 演示完成！")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
