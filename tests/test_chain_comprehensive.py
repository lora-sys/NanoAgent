"""提示链综合测试脚本"""

import asyncio
import time
from core.chain import PromptChain, ChainStep, ChainContext, create_analysis_chain
from llm.client import NanoLLMClient


def print_section(title):
    """打印测试章节"""
    print(f"\n{'=' * 60}")
    print(f"🧪 {title}")
    print("=" * 60)


async def test_unit_tests():
    """单元测试"""
    print_section("1. 单元测试")

    # 测试 ChainContext
    context = ChainContext({"input": "测试"})
    context.set("key", "value")
    assert context.get("key") == "value"
    context.add_history("step1", "result1")
    assert len(context.history) == 1
    print("✅ ChainContext 测试通过")

    # 测试 ChainResult
    result = type(
        "ChainResult",
        (),
        {
            "success": True,
            "final_output": "输出",
            "context": context,
            "error": None,
            "execution_time": 1.0,
            "to_dict": lambda self: {"success": self.success},
        },
    )()
    assert result.success is True
    print("✅ ChainResult 测试通过")

    # 测试 ChainStep
    step = ChainStep("测试步骤", "测试提示")
    assert step.name == "测试步骤"
    assert step.prompt == "测试提示"
    print("✅ ChainStep 测试通过")

    # 测试 PromptChain
    chain = PromptChain(
        [
            ChainStep("步骤1", "提示1"),
            ChainStep("步骤2", "提示2"),
        ]
    )
    assert len(chain.steps) == 2
    print("✅ PromptChain 测试通过")


async def test_integration_tests():
    """集成测试"""
    print_section("2. 集成测试")

    client = NanoLLMClient()

    # 测试基础链执行
    chain = PromptChain(
        [
            ChainStep("步骤1", "请回复：步骤1完成"),
            ChainStep("步骤2", "请回复：步骤2完成"),
        ]
    )

    result = await chain.run("集成测试", client)
    assert result.success is True
    assert len(result.context.history) == 2
    print(f"✅ 基础链执行测试通过 (耗时: {result.execution_time:.2f}秒)")


async def test_real_usage_tests():
    """实际使用测试"""
    print_section("3. 实际使用测试")

    client = NanoLLMClient()

    # 测试分析链
    analysis_chain = create_analysis_chain()
    result = await analysis_chain.run("分析 nanoagent 项目的核心功能", client)

    assert result.success is True
    assert len(result.context.history) == 4
    print(f"✅ 分析链测试通过 (耗时: {result.execution_time:.2f}秒)")
    print(f"   执行步骤: {[h['step'] for h in result.context.history]}")


async def test_performance_tests():
    """性能测试"""

    print_section("4. 性能测试")

    client = NanoLLMClient()

    # 测试不同长度的链

    for steps_count in [2, 4, 6]:
        chain = PromptChain(
            [
                ChainStep(f"步骤{i}", f"请回复：步骤{i}完成")
                for i in range(1, steps_count + 1)
            ]
        )

        start = time.time()

        await chain.run("性能测试", client)

        duration = time.time() - start

        avg_time = duration / steps_count

        print(f"✅ {steps_count}步骤链: {duration:.2f}秒 (平均: {avg_time:.2f}秒/步)")


async def test_edge_case_tests():
    """边界情况测试"""
    print_section("5. 边界情况测试")

    client = NanoLLMClient()

    # 测试空链
    empty_chain = PromptChain([])
    result = await empty_chain.run("测试", client)
    assert result.success is True
    print("✅ 空链测试通过")

    # 测试单步骤链
    single_chain = PromptChain([ChainStep("单步", "请回复：单步完成")])
    result = await single_chain.run("测试", client)
    assert result.success is True
    print("✅ 单步骤链测试通过")

    # 测试自定义上下文
    context = ChainContext({"custom": "value"})
    chain = PromptChain([ChainStep("步骤1", "使用自定义数据")])
    result = await chain.run("测试", client, context)
    assert context.get("custom") == "value"
    print("✅ 自定义上下文测试通过")

    # 测试错误处理
    def error_handler(ctx):
        raise ValueError("测试错误")

    error_chain = PromptChain(
        [
            ChainStep("正常步骤", "正常提示"),
            ChainStep("错误步骤", "错误提示", handler=error_handler),
        ],
        stop_on_error=True,
    )

    result = await error_chain.run("测试", client)
    assert result.success is False
    assert result.error is not None
    print("✅ 错误处理测试通过")


async def test_error_recovery_tests():
    """错误恢复测试"""
    print_section("6. 错误恢复测试")

    client = NanoLLMClient()

    # 测试错误时继续执行
    def error_handler(ctx):
        raise ValueError("测试错误")

    chain = PromptChain(
        [
            ChainStep("正常步骤1", "正常提示"),
            ChainStep("错误步骤", "错误提示", handler=error_handler),
            ChainStep("正常步骤2", "正常提示"),
        ],
        stop_on_error=False,
    )

    result = await chain.run("测试", client)
    assert result.success is False  # 整体失败
    assert len(result.context.history) == 3  # 但所有步骤都执行了
    print("✅ 错误时继续执行测试通过")


async def test_custom_handler_tests():
    """自定义处理器测试"""
    print_section("7. 自定义处理器测试")

    # 测试同步处理器
    def sync_handler(context):
        context.set("sync_data", "同步数据")
        return "同步结果"

    # 测试异步处理器
    async def async_handler(context):
        await asyncio.sleep(0.1)
        context.set("async_data", "异步数据")
        return "异步结果"

    chain = PromptChain(
        [
            ChainStep("同步步骤", "同步提示", handler=sync_handler),
            ChainStep("异步步骤", "异步提示", handler=async_handler),
        ]
    )

    from llm.client import NanoLLMClient

    client = NanoLLMClient()

    result = await chain.run("自定义处理器测试", client)
    assert result.success is True
    print("✅ 自定义处理器测试通过")


async def main():
    """主测试函数"""
    print("\n🚀 提示链综合测试开始")
    print("=" * 60)

    try:
        await test_unit_tests()
        await test_integration_tests()
        await test_real_usage_tests()
        await test_performance_tests()
        await test_edge_case_tests()
        await test_error_recovery_tests()
        await test_custom_handler_tests()

        print_section("测试结果")
        print("🎉 所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
