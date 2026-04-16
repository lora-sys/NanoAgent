"""提示链示例 - 展示如何使用提示链处理复杂任务"""

import asyncio
from core.chain import PromptChain, ChainStep, ChainContext, create_analysis_chain


class MockLLMClient:
    """Mock LLM 客户端用于演示"""

    def chat(self, messages):
        content = messages[0]["content"]
        if "步骤1" in content:
            return "步骤1执行完成"
        elif "步骤2" in content:
            return "步骤2执行完成"
        elif "步骤3" in content:
            return "步骤3执行完成"
        elif "分析需求" in content:
            return '{"requirement": "分析项目代码结构", "goals": ["理解架构", "识别关键组件"], "constraints": ["时间有限"]}'
        elif "制定计划" in content:
            return '{"steps": [{"step": "阅读代码", "description": "分析主要文件"}], "estimated_time": "30分钟"}'
        elif "执行分析" in content:
            return "完成代码分析，发现3个核心模块"
        elif "总结结果" in content:
            return "项目采用模块化设计，核心功能清晰，可维护性良好"
        return "未知步骤"

    async def achat(self, messages):
        return self.chat(messages)


async def demo_basic_chain():
    """演示基础提示链使用"""
    print("🎯 基础提示链示例")

    # 创建简单的提示链
    chain = PromptChain(
        [
            ChainStep("步骤1", "请执行第一个步骤"),
            ChainStep("步骤2", "请执行第二个步骤"),
            ChainStep("步骤3", "请执行第三个步骤"),
        ]
    )

    client = MockLLMClient()

    # 执行提示链
    result = await chain.run("处理这个任务", client)

    print(f"✅ 执行状态: {result.success}")
    print(f"⏱️ 执行时间: {result.execution_time:.2f}秒")
    print(f"📊 执行步骤数: {len(result.context.history)}")
    print(f"🎯 最终输出: {result.final_output}")
    print()


async def demo_analysis_chain():
    """演示分析任务提示链"""
    print("🎯 分析任务提示链示例")

    # 使用预定义的分析链
    chain = create_analysis_chain()
    client = MockLLMClient()

    # 执行分析任务
    result = await chain.run("分析这个项目的代码结构", client)

    print(f"✅ 执行状态: {result.success}")
    print(f"⏱️ 执行时间: {result.execution_time:.2f}秒")
    print("📋 执行步骤:")
    for i, history in enumerate(result.context.history, 1):
        print(f"  {i}. {history['step']}: {history['result'][:50]}...")
    print()


async def demo_custom_handler():
    """演示自定义处理器"""
    print("🎯 自定义处理器示例")

    # 自定义处理器
    def custom_step1(context):
        print("  📌 执行自定义步骤1...")
        context.set("data1", "自定义数据1")
        return "步骤1结果"

    def custom_step2(context):
        print("  📌 执行自定义步骤2...")
        data1 = context.get("data1")
        context.set("data2", f"{data1} + 自定义数据2")
        return "步骤2结果"

    # 创建带自定义处理器的提示链
    chain = PromptChain(
        [
            ChainStep("自定义步骤1", "提示1", handler=custom_step1),
            ChainStep("自定义步骤2", "提示2", handler=custom_step2),
        ]
    )

    client = MockLLMClient()

    # 执行提示链
    result = await chain.run("使用自定义处理器", client)

    print(f"✅ 执行状态: {result.success}")
    print(f"📊 上下文数据: {result.context.data}")
    print()


async def demo_error_handling():
    """演示错误处理"""
    print("🎯 错误处理示例")

    # 创建会出错的步骤
    def error_step(context):
        raise ValueError("模拟错误")

    chain = PromptChain(
        [
            ChainStep("正常步骤", "正常提示"),
            ChainStep("错误步骤", "错误提示", handler=error_step),
            ChainStep("后续步骤", "后续提示"),
        ],
        stop_on_error=False,
    )  # 错误时继续执行

    client = MockLLMClient()

    # 执行提示链
    result = await chain.run("测试错误处理", client)

    print(f"✅ 执行状态: {result.success}")
    print(f"❌ 错误信息: {result.error}")
    print(f"📊 执行步骤数: {len(result.context.history)} (即使出错也继续执行)")
    print()


async def demo_context_sharing():
    """演示上下文共享"""
    print("🎯 上下文共享示例")

    # 创建共享上下文
    context = ChainContext({"project": "nanoagent", "goal": "代码分析"})

    # 创建提示链
    chain = PromptChain(
        [
            ChainStep("步骤1", "分析项目 {project}，目标是 {goal}"),
            ChainStep("步骤2", "基于步骤1结果继续分析"),
        ]
    )

    client = MockLLMClient()

    # 执行提示链
    result = await chain.run("使用共享上下文", client, context)

    print(f"✅ 执行状态: {result.success}")
    print(f"📊 共享上下文: {result.context.data}")
    print()


async def main():
    """主函数"""
    print("🚀 提示链示例演示\n")
    print("=" * 50)
    print()

    await demo_basic_chain()
    await demo_analysis_chain()
    await demo_custom_handler()
    await demo_error_handling()
    await demo_context_sharing()

    print("=" * 50)
    print("🎉 所有演示完成！")


if __name__ == "__main__":
    asyncio.run(main())
