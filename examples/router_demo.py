"""路由模块示例 - 展示智能路由的使用方法"""

import asyncio
from core.router import Router, RouteContext


class MockLLMClient:
    """Mock LLM 客户端用于演示"""

    def chat(self, messages):
        content = messages[0]["content"]
        if "数据库" in content:
            return '{"target": "database", "reasoning": "任务涉及数据库查询", "confidence": 0.9}'
        elif "搜索" in content:
            return '{"target": "search", "reasoning": "任务需要搜索功能", "confidence": 0.85}'
        elif "分析" in content:
            return '{"target": "analysis", "reasoning": "任务需要数据分析", "confidence": 0.92}'
        return '{"target": "general", "reasoning": "通用任务", "confidence": 0.7}'

    async def achat(self, messages):
        return self.chat(messages)


async def demo_basic_routing():
    """演示基本路由"""
    print("🎯 场景1：基本路由")
    print("=" * 50)

    # 创建路由器
    router = Router("basic_router", default_target="general")

    # 添加路由规则
    router.add_route(
        name="数据库路由",
        target="database",
        condition="数据库",
        priority=1,
        description="处理数据库相关任务",
    ).add_route(
        name="搜索路由",
        target="search",
        condition="搜索",
        priority=1,
        description="处理搜索相关任务",
    ).add_route(
        name="分析路由",
        target="analysis",
        condition="分析",
        priority=1,
        description="处理分析相关任务",
    )

    # 测试路由
    tasks = ["查询数据库中的用户信息", "搜索相关的内容", "分析销售数据", "其他任务"]

    for task in tasks:
        decision = await router.route(task)
        print(f"任务: {task}")
        print(f"  → 目标: {decision.target}")
        print(f"  → 原因: {decision.reasoning}")
        print(f"  → 置信度: {decision.confidence}")
        print()


async def demo_priority_routing():
    """演示优先级路由"""
    print("🎯 场景2：优先级路由")
    print("=" * 50)

    # 创建路由器
    router = Router("priority_router", default_target="default")

    # 添加不同优先级的路由
    router.add_route(
        name="高优先级路由",
        target="high_priority",
        condition="紧急",
        priority=10,
        description="处理紧急任务",
    ).add_route(
        name="中优先级路由",
        target="medium_priority",
        condition="重要",
        priority=5,
        description="处理重要任务",
    ).add_route(
        name="低优先级路由",
        target="low_priority",
        condition="普通",
        priority=1,
        description="处理普通任务",
    )

    # 测试路由
    tasks = ["紧急修复系统bug", "重要功能开发", "普通文档更新"]

    for task in tasks:
        decision = await router.route(task)
        print(f"任务: {task}")
        print(f"  → 目标: {decision.target}")
        print(f"  → 原因: {decision.reasoning}")
        print()


async def demo_custom_function_routing():
    """演示自定义函数路由"""
    print("🎯 场景3：自定义函数路由")
    print("=" * 50)

    # 自定义路由函数
    def route_by_length(task: str) -> bool:
        """根据任务长度路由"""
        return len(task) > 20

    def route_by_keyword_count(task: str) -> bool:
        """根据关键词数量路由"""
        keywords = ["分析", "设计", "开发", "测试"]
        return sum(1 for kw in keywords if kw in task) >= 2

    # 创建路由器
    router = Router("custom_router", default_target="simple")

    # 添加自定义函数路由
    router.add_route(
        name="复杂任务路由",
        target="complex",
        condition=route_by_keyword_count,
        priority=5,
        description="处理包含多个关键词的复杂任务",
    ).add_route(
        name="长任务路由",
        target="long",
        condition=route_by_length,
        priority=3,
        description="处理长任务描述",
    )

    # 测试路由
    tasks = [
        "分析并设计开发测试流程",
        "这是一个很长的任务描述，需要详细处理",
        "简单任务",
    ]

    for task in tasks:
        decision = await router.route(task)
        print(f"任务: {task}")
        print(f"  → 目标: {decision.target}")
        print(f"  → 原因: {decision.reasoning}")
        print()


async def demo_smart_routing():
    """演示智能路由（使用 LLM）"""
    print("🎯 场景4：智能路由（使用 LLM）")
    print("=" * 50)

    # 创建智能路由器
    router = Router("smart_router", default_target="general", use_llm_routing=True)

    # 添加基本路由规则
    router.add_route(
        name="数据库路由", target="database", condition="数据库", priority=1
    ).add_route(name="搜索路由", target="search", condition="搜索", priority=1)

    # 设置 LLM 客户端
    llm_client = MockLLMClient()
    router.set_llm_client(llm_client)

    # 测试智能路由
    tasks = ["查询数据库中的用户信息", "搜索相关的内容", "分析销售数据趋势"]

    for task in tasks:
        decision = await router.route(task)
        print(f"任务: {task}")
        print(f"  → 目标: {decision.target}")
        print(f"  → 原因: {decision.reasoning}")
        print(f"  → 置信度: {decision.confidence}")
        print(f"  → 路由类型: {decision.metadata.get('route_type', 'unknown')}")
        print()


async def demo_route_context():
    """演示路由上下文"""
    print("🎯 场景5：路由上下文")
    print("=" * 50)

    # 创建路由器
    router = Router("context_router", default_target="default")

    # 添加路由
    router.add_route(
        name="数据库路由", target="database", condition="数据库"
    ).add_route(name="搜索路由", target="search", condition="搜索")

    # 创建路由上下文
    context = RouteContext({"user_id": "123", "session_id": "abc"})

    # 执行多次路由
    tasks = ["查询数据库", "搜索内容", "再次查询数据库"]

    for task in tasks:
        decision = await router.route(task, context)
        print(f"任务: {task}")
        print(f"  → 目标: {decision.target}")

    # 查看路由历史
    print(f"\n📊 路由历史: {len(context.history)} 次")
    for i, history in enumerate(context.history, 1):
        print(f"  {i}. {history['task']} → {history['decision']['target']}")
    print()


async def demo_real_world_scenario():
    """演示真实世界场景"""
    print("🎯 场景6：真实世界 - 电商系统路由")
    print("=" * 50)

    # 创建电商系统路由器
    router = Router("ecommerce_router", default_target="general")

    # 添加路由规则
    router.add_route(
        name="商品查询路由",
        target="product_service",
        condition="商品",
        priority=5,
        description="处理商品相关查询",
    ).add_route(
        name="订单管理路由",
        target="order_service",
        condition="订单",
        priority=5,
        description="处理订单相关操作",
    ).add_route(
        name="用户服务路由",
        target="user_service",
        condition="用户",
        priority=5,
        description="处理用户相关请求",
    ).add_route(
        name="支付路由",
        target="payment_service",
        condition="支付",
        priority=10,
        description="处理支付相关操作（高优先级）",
    ).add_route(
        name="搜索路由",
        target="search_service",
        condition="搜索",
        priority=3,
        description="处理搜索请求",
    )

    # 模拟用户请求
    requests = ["查询商品信息", "创建订单", "用户登录", "支付订单", "搜索商品"]

    print("处理用户请求:")
    for request in requests:
        decision = await router.route(request)
        print(f"  请求: {request}")
        print(f"  → 服务: {decision.target}")
        print()

    # 显示路由器信息
    print("📊 路由器信息:")
    info = router.get_route_info()
    print(f"  名称: {info['name']}")
    print(f"  路由数量: {info['route_count']}")
    print(f"  默认目标: {info['default_target']}")
    print()


async def main():
    """主函数"""
    print("🚀 路由模块示例演示")
    print("=" * 50)
    print()

    await demo_basic_routing()
    await demo_priority_routing()
    await demo_custom_function_routing()
    await demo_smart_routing()
    await demo_route_context()
    await demo_real_world_scenario()

    print("=" * 50)
    print("🎉 所有示例演示完成！")
    print()
    print("💡 路由模块适用于：")
    print("  - 任务分发和路由")
    print("  - 多服务系统协调")
    print("  - 智能任务分类")
    print("  - 优先级任务处理")
    print("  - 复杂工作流管理")


if __name__ == "__main__":
    asyncio.run(main())
