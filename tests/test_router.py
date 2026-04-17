"""路由模块测试"""

import pytest
from core.router import (
    Router,
    RouteDecision,
    Route,
    RouteContext,
    create_simple_router,
    create_smart_router,
)


class MockLLMClient:
    """Mock LLM 客户端用于测试"""

    def chat(self, messages):
        content = messages[0]["content"]
        if "数据库" in content:
            return '{"target": "database", "reasoning": "任务涉及数据库查询", "confidence": 0.9}'
        elif "搜索" in content:
            return '{"target": "search", "reasoning": "任务需要搜索功能", "confidence": 0.85}'
        return '{"target": "general", "reasoning": "通用任务", "confidence": 0.7}'

    async def achat(self, messages):
        return self.chat(messages)


class TestRouteDecision:
    """测试 RouteDecision"""

    def test_route_decision_creation(self):
        """测试创建路由决策"""
        decision = RouteDecision(
            target="database",
            reasoning="数据库查询",
            confidence=0.9,
            metadata={"route_type": "keyword"},
        )

        assert decision.target == "database"
        assert decision.reasoning == "数据库查询"
        assert decision.confidence == 0.9
        assert decision.metadata["route_type"] == "keyword"

    def test_route_decision_to_dict(self):
        """测试路由决策转换为字典"""
        decision = RouteDecision(target="search", reasoning="搜索任务", confidence=0.85)
        result = decision.to_dict()

        assert result["target"] == "search"
        assert result["reasoning"] == "搜索任务"
        assert result["confidence"] == 0.85
        assert "metadata" in result


class TestRoute:
    """测试 Route"""

    def test_route_with_string_condition(self):
        """测试字符串条件路由"""
        route = Route(
            name="数据库路由",
            target="database",
            condition="数据库",
            priority=1,
        )

        assert route.matches("查询数据库")
        assert route.matches("数据库操作")
        assert not route.matches("搜索内容")

    def test_route_with_function_condition(self):
        """测试函数条件路由"""

        def condition(task: str) -> bool:
            return len(task) > 5

        route = Route(name="长任务路由", target="long", condition=condition)

        assert route.matches("这是一个很长的任务")
        assert not route.matches("短")

    def test_route_matches_case_insensitive(self):
        """测试路由匹配不区分大小写"""
        route = Route(name="测试路由", target="test", condition="test")

        assert route.matches("这是一个test")
        assert route.matches("这是一个TEST")
        assert route.matches("这是一个TeSt")


class TestRouteContext:
    """测试 RouteContext"""

    def test_route_context_creation(self):
        """测试创建路由上下文"""
        context = RouteContext({"user_id": "123"})

        assert context.get("user_id") == "123"
        assert context.get("nonexistent") is None
        assert context.get("nonexistent", "default") == "default"

    def test_route_context_set_get(self):
        """测试设置和获取上下文数据"""
        context = RouteContext()

        context.set("key1", "value1")
        context.set("key2", 123)

        assert context.get("key1") == "value1"
        assert context.get("key2") == 123

    def test_route_context_add_history(self):
        """测试添加路由历史"""
        context = RouteContext()
        decision = RouteDecision(target="database", reasoning="测试", confidence=0.9)

        context.add_history(decision, "测试任务")

        assert len(context.history) == 1
        assert context.history[0]["task"] == "测试任务"
        assert context.history[0]["decision"]["target"] == "database"

    def test_route_context_to_dict(self):
        """测试路由上下文转换为字典"""
        context = RouteContext({"key": "value"})
        decision = RouteDecision(target="test", reasoning="测试", confidence=0.8)

        context.add_history(decision, "任务")

        result = context.to_dict()

        assert "data" in result
        assert "history" in result
        assert "metadata" in result
        assert result["data"]["key"] == "value"


class TestRouter:
    """测试 Router"""

    @pytest.mark.asyncio
    async def test_router_creation(self):
        """测试创建路由器"""
        router = Router("test_router", default_target="default")

        assert router.name == "test_router"
        assert router.default_target == "default"
        assert len(router.routes) == 0

    @pytest.mark.asyncio
    async def test_add_route(self):
        """测试添加路由"""
        router = Router("test_router")

        router.add_route(
            name="数据库路由",
            target="database",
            condition="数据库",
            priority=1,
        )

        assert len(router.routes) == 1
        assert router.routes[0].name == "数据库路由"

    @pytest.mark.asyncio
    async def test_add_route_chaining(self):
        """测试链式添加路由"""
        router = Router("test_router")

        router.add_route("路由1", "target1", "条件1").add_route(
            "路由2", "target2", "条件2"
        )

        assert len(router.routes) == 2

    @pytest.mark.asyncio
    async def test_route_by_keywords(self):
        """测试关键词路由"""
        router = Router("test_router", default_target="default")

        router.add_route("数据库路由", "database", "数据库").add_route(
            "搜索路由", "search", "搜索"
        )

        decision1 = await router.route("查询数据库")
        decision2 = await router.route("搜索内容")
        decision3 = await router.route("其他任务")

        assert decision1.target == "database"
        assert decision2.target == "search"
        assert decision3.target == "default"

    @pytest.mark.asyncio
    async def test_route_priority(self):
        """测试路由优先级"""
        router = Router("test_router", default_target="default")

        router.add_route("低优先级", "low", "条件", priority=1).add_route(
            "高优先级", "high", "条件", priority=10
        )

        decision = await router.route("条件任务")

        assert decision.target == "high"

    @pytest.mark.asyncio
    async def test_route_with_custom_function(self):
        """测试自定义函数路由"""
        router = Router("test_router", default_target="default")

        def condition(task: str) -> bool:
            return len(task) > 10

        router.add_route("长任务路由", "long", condition)

        decision1 = await router.route("这是一个很长的任务描述")
        decision2 = await router.route("短任务")

        assert decision1.target == "long"
        assert decision2.target == "default"

    @pytest.mark.asyncio
    async def test_smart_routing_with_llm(self):
        """测试智能路由（使用 LLM）"""
        router = Router("smart_router", default_target="general", use_llm_routing=True)

        router.add_route("数据库路由", "database", "数据库")

        llm_client = MockLLMClient()
        router.set_llm_client(llm_client)

        # 关键词匹配应该优先
        decision1 = await router.route("查询数据库")
        assert decision1.target == "database"
        assert decision1.metadata.get("route_type") == "keyword"

        # 无关键词匹配时使用 LLM
        decision2 = await router.route("分析销售数据")
        assert decision2.target == "general"
        assert decision2.metadata.get("route_type") == "llm"

    @pytest.mark.asyncio
    async def test_route_context_tracking(self):
        """测试路由上下文跟踪"""
        router = Router("test_router")

        router.add_route("数据库路由", "database", "数据库").add_route(
            "搜索路由", "search", "搜索"
        )

        context = RouteContext()

        await router.route("查询数据库", context)
        await router.route("搜索内容", context)
        await router.route("查询数据库", context)

        assert len(context.history) == 3
        assert context.history[0]["decision"]["target"] == "database"
        assert context.history[1]["decision"]["target"] == "search"
        assert context.history[2]["decision"]["target"] == "database"

    def test_route_sync(self):
        """测试同步路由"""
        router = Router("test_router", default_target="default")

        router.add_route("数据库路由", "database", "数据库")

        decision = router.route_sync("查询数据库")

        assert decision.target == "database"

    def test_get_route_info(self):
        """测试获取路由器信息"""
        router = Router("test_router", default_target="default")

        router.add_route("路由1", "target1", "条件1", priority=1).add_route(
            "路由2", "target2", "条件2", priority=5
        )

        info = router.get_route_info()

        assert info["name"] == "test_router"
        assert info["default_target"] == "default"
        assert info["route_count"] == 2
        assert len(info["routes"]) == 2


class TestRouterFactories:
    """测试路由器工厂函数"""

    def test_create_simple_router(self):
        """测试创建简单路由器"""
        router = create_simple_router()

        assert router.name == "simple_router"
        assert router.default_target == "general"
        assert router.use_llm_routing is False

    def test_create_smart_router(self):
        """测试创建智能路由器"""
        router = create_smart_router()

        assert router.name == "smart_router"
        assert router.default_target == "general"
        assert router.use_llm_routing is True

    def test_create_smart_router_with_custom_default(self):
        """测试创建带自定义默认目标的智能路由器"""
        router = create_smart_router(default_target="custom")

        assert router.default_target == "custom"


@pytest.mark.asyncio
async def test_real_world_scenario():
    """测试真实世界场景"""
    # 电商系统路由器
    router = Router("ecommerce_router", default_target="general")

    router.add_route("商品路由", "product", "商品", priority=5).add_route(
        "订单路由", "order", "订单", priority=5
    ).add_route("用户路由", "user", "用户", priority=5).add_route(
        "支付路由", "payment", "支付", priority=10
    )

    # 测试各种请求
    requests = [
        ("查询商品信息", "product"),
        ("创建订单", "order"),
        ("用户登录", "user"),
        ("支付订单", "payment"),
    ]

    for request, expected_target in requests:
        decision = await router.route(request)
        assert decision.target == expected_target


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
