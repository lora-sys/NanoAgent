"""可组合模块使用示例 - 展示如何灵活拼装功能"""

import asyncio
from core.composable import AgentBuilder
from core.router import Router
from core.chain import PromptChain, ChainStep


async def demo_basic_usage():
    """基础使用示例"""
    print("🎯 基础使用示例")
    print("=" * 50)

    # 使用构建器创建 Agent
    agent = AgentBuilder().build()

    # 执行简单任务
    result = await agent.execute("你好")
    print(f"✅ 执行结果: {result}")
    print()


async def demo_with_router():
    """使用路由器"""
    print("🧭 使用路由器示例")
    print("=" * 50)

    # 创建路由器
    router = Router("demo_router", default_target="general")
    router.add_route("技术路由", "tech", "技术", priority=10)
    router.add_route("业务路由", "business", "业务", priority=5)

    # 创建带路由器的 Agent
    agent = AgentBuilder().with_router(router).build()

    # 执行任务
    result = await agent.execute("处理技术问题", use_router=True)
    print(f"✅ 路由到: {result['routing_decision']['target']}")
    print()


async def demo_with_chain():
    """使用提示链"""
    print("🔗 使用提示链示例")
    print("=" * 50)

    # 创建提示链
    chain = PromptChain(
        [
            ChainStep("步骤1", "执行第一步"),
            ChainStep("步骤2", "执行第二步"),
        ]
    )

    # 创建带提示链的 Agent
    agent = AgentBuilder().with_chain(chain).build()

    # 执行任务
    result = await agent.execute("创建文档", use_chain=True)
    print(f"✅ 执行路径: {result['execution_path']}")
    print()


async def demo_full_features():
    """完整功能示例"""
    print("🚀 完整功能示例")
    print("=" * 50)

    # 创建路由器
    router = Router("full_router", default_target="general")
    router.add_route("技术路由", "tech", "技术", priority=10)

    # 创建提示链
    chain = PromptChain(
        [
            ChainStep("分析", "分析需求"),
            ChainStep("设计", "设计方案"),
        ]
    )

    # 创建完整功能的 Agent
    agent = AgentBuilder().with_router(router).with_chain(chain).build()

    # 执行任务
    result = await agent.execute(
        "分析技术架构",
        use_router=True,
        use_chain=True,
    )

    print(f"✅ 执行路径: {' -> '.join(result['execution_path'])}")
    print(f"🔧 使用的功能: {', '.join(result['features_used'])}")
    print()


async def main():
    """主函数"""
    print("🚀 可组合模块演示\n")

    await demo_basic_usage()
    await demo_with_router()
    await demo_with_chain()
    await demo_full_features()

    print("=" * 50)
    print("🎉 所有演示完成！")

    print("\n💡 可组合模块的特点:")
    print("  - 模块化设计，可以随意拼装")
    print("  - 流式 API，易于使用")
    print("  - 支持功能动态切换")
    print("  - 符合框架设计原则")


if __name__ == "__main__":
    asyncio.run(main())
