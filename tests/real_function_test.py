"""真实功能测试 - 使用真实 LLM 验证系统功能"""

import asyncio
from core.router import Router
from core.chain import PromptChain, ChainStep
from core.agent import NanoAgent
from llm.client import NanoLLMClient


async def test_router_with_real_llm():
    """测试路由功能（使用真实 LLM）"""
    print("🧭 测试路由功能（真实 LLM）")
    print("=" * 50)

    # 创建路由器
    router = Router("test_router", default_target="general")

    # 添加路由规则
    router.add_route("数据库路由", "database", "数据库", priority=5).add_route(
        "搜索路由", "search", "搜索", priority=5
    ).add_route("分析路由", "analysis", "分析", priority=5).add_route(
        "订单路由", "order", "订单", priority=5
    )

    # 测试提示词
    test_prompts = [
        "查询数据库中的用户信息",
        "搜索相关的内容",
        "分析销售数据",
        "创建新订单",
        "处理其他任务",
    ]

    print("测试提示词:")
    for prompt in test_prompts:
        decision = await router.route(prompt)
        print(f"  提示词: {prompt}")
        print(f"  → 路由到: {decision.target}")
        print(f"  → 原因: {decision.reasoning}")
        print(f"  → 置信度: {decision.confidence}")
        print()


async def test_chain_with_real_llm():
    """测试提示链功能（使用真实 LLM）"""
    print("🔗 测试提示链功能（真实 LLM）")
    print("=" * 50)

    # 创建提示链
    chain = PromptChain(
        [
            ChainStep("需求分析", "分析用户需求，明确目标和约束条件"),
            ChainStep("方案设计", "基于需求分析结果，设计技术方案"),
            ChainStep("实施建议", "基于设计方案，提供具体的实施建议"),
        ]
    )

    # 创建真实 LLM 客户端
    llm_client = NanoLLMClient()

    # 测试提示词
    test_prompt = "设计一个简单的博客系统"

    print(f"测试提示词: {test_prompt}")
    print()

    try:
        # 执行提示链
        result = await chain.run(test_prompt, llm_client)

        print(f"✅ 执行状态: {'成功' if result.success else '失败'}")
        print(f"⏱️ 执行时间: {result.execution_time:.2f}秒")
        print(f"📋 执行步骤数: {len(result.context.history)}")
        print()

        print("执行步骤详情:")
        for i, history in enumerate(result.context.history, 1):
            print(f"  步骤{i}: {history['step']}")
            print(f"  结果: {history['result'][:200]}...")
            print()

        print(f"最终输出: {result.final_output[:300]}...")
    except Exception as e:
        print(f"❌ 执行失败: {str(e)}")


async def test_agent_with_real_llm():
    """测试基础 Agent 功能（使用真实 LLM）"""
    print("🤖 测试基础 Agent 功能（真实 LLM）")
    print("=" * 50)

    # 创建 Agent
    agent = NanoAgent()

    # 测试提示词
    test_prompts = [
        "用一句话介绍 Python 编程语言",
        "什么是异步编程？",
    ]

    for prompt in test_prompts:
        print(f"测试提示词: {prompt}")
        print()

        try:
            # 执行任务
            result = agent.run(prompt, max_iterations=3)

            print(f"✅ 状态: {result.get('status', 'unknown')}")
            print(f"🔄 迭代次数: {result.get('iterations', 0)}")
            print(f"🔧 使用的工具: {result.get('tools_used', [])}")
            print()

        except Exception as e:
            print(f"❌ 执行失败: {str(e)}")
        print()


async def test_complex_scenario_with_real_llm():
    """测试复杂场景（使用真实 LLM）"""
    print("🎯 测试复杂场景（真实 LLM）")
    print("=" * 50)

    # 创建电商系统路由器
    router = Router("ecommerce_router", default_target="general")

    router.add_route("商品路由", "product", "商品", priority=5).add_route(
        "订单路由", "order", "订单", priority=5
    ).add_route("用户路由", "user", "用户", priority=5).add_route(
        "支付路由", "payment", "支付", priority=10
    ).add_route("购物车路由", "product", "购物车", priority=5)

    # 复杂业务流程
    business_flow = [
        "用户登录系统",
        "搜索商品信息",
        "查看商品详情",
        "添加到购物车",
        "创建订单",
        "处理支付",
    ]

    print("电商业务流程测试:")
    for step in business_flow:
        decision = await router.route(step)
        print(f"  {step} → {decision.target} ({decision.reasoning})")

    print()


async def main():
    """主函数"""
    print("🚀 开始真实功能测试")
    print("=" * 50)
    print()

    # 1. 测试路由功能
    await test_router_with_real_llm()

    print("\n" + "=" * 50 + "\n")

    # 2. 测试提示链功能
    await test_chain_with_real_llm()

    print("\n" + "=" * 50 + "\n")

    # 3. 测试基础 Agent 功能
    await test_agent_with_real_llm()

    print("\n" + "=" * 50 + "\n")

    # 4. 测试复杂场景
    await test_complex_scenario_with_real_llm()

    print("=" * 50)
    print("🎉 真实功能测试完成！")
    print()
    print("💡 测试总结:")
    print("  - 路由功能：验证任务分发能力")
    print("  - 提示链功能：验证复杂任务处理")
    print("  - Agent 功能：验证基础执行能力")
    print("  - 复杂场景：验证系统集成能力")
    print()
    print("⚠️ 注意：真实测试会产生 API 调用成本")


if __name__ == "__main__":
    asyncio.run(main())
