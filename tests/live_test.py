"""实时测试 - 验证系统功能的准确性"""

import asyncio
import json
from typing import Dict, List, Any
from core.router import Router, RouteContext
from core.chain import PromptChain, ChainStep, ChainContext


class LiveTestRunner:
    """实时测试运行器"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0

    def log_result(
        self,
        test_name: str,
        passed: bool,
        expected: Any,
        actual: Any,
        details: str = "",
    ):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "expected": str(expected),
            "actual": str(actual),
            "details": details,
        }
        self.results.append(result)

        if passed:
            self.passed += 1
            print(f"✅ {test_name}")
        else:
            self.failed += 1
            print(f"❌ {test_name}")
            print(f"   期望: {expected}")
            print(f"   实际: {actual}")
            if details:
                print(f"   详情: {details}")

    def print_summary(self):
        """打印测试摘要"""
        total = self.passed + self.failed
        print(f"\n📊 测试摘要: {self.passed}/{total} 通过")
        if self.failed > 0:
            print(f"❌ 失败: {self.failed}")
        else:
            print("🎉 所有测试通过！")


async def test_router_functionality(runner: LiveTestRunner):
    """测试路由功能"""
    print("\n🧭 测试路由功能")
    print("=" * 50)

    # 创建路由器
    router = Router("test_router", default_target="general")

    # 添加路由规则
    router.add_route("数据库路由", "database", "数据库", priority=5).add_route(
        "搜索路由", "search", "搜索", priority=5
    ).add_route("分析路由", "analysis", "分析", priority=5).add_route(
        "订单路由", "order", "订单", priority=8
    ).add_route("支付路由", "payment", "支付", priority=10)

    # 测试用例
    test_cases = [
        ("查询数据库中的用户信息", "database"),
        ("搜索相关的内容", "search"),
        ("分析销售数据", "analysis"),
        ("创建新订单", "order"),
        ("处理支付请求", "payment"),
        ("其他普通任务", "general"),
    ]

    for task, expected in test_cases:
        decision = await router.route(task)
        runner.log_result(
            f"路由测试: {task[:20]}...",
            decision.target == expected,
            expected,
            decision.target,
            decision.reasoning,
        )


async def test_router_with_priority(runner: LiveTestRunner):
    """测试路由优先级"""
    print("\n🧭 测试路由优先级")
    print("=" * 50)

    router = Router("priority_router", default_target="default")

    # 添加不同优先级的路由
    router.add_route("普通路由", "normal", "任务", priority=1).add_route(
        "重要路由", "important", "重要", priority=5
    ).add_route("紧急路由", "urgent", "紧急", priority=10)

    # 测试包含多个关键词的任务
    task = "这是一个紧急重要的任务"
    decision = await router.route(task)

    # 应该选择最高优先级的路由
    runner.log_result(
        "优先级测试: 紧急任务",
        decision.target == "urgent",
        "urgent",
        decision.target,
        decision.reasoning,
    )


async def test_chain_functionality(runner: LiveTestRunner):
    """测试提示链功能"""
    print("\n🔗 测试提示链功能")
    print("=" * 50)

    # 创建简单的提示链
    chain = PromptChain(
        [
            ChainStep("步骤1", "执行第一个步骤"),
            ChainStep("步骤2", "执行第二个步骤"),
            ChainStep("步骤3", "执行第三个步骤"),
        ]
    )

    # Mock LLM 客户端
    class MockLLMClient:
        def chat(self, messages):
            content = messages[0]["content"]
            if "步骤1" in content:
                return "步骤1完成"
            elif "步骤2" in content:
                return "步骤2完成"
            elif "步骤3" in content:
                return "步骤3完成"
            return "未知步骤"

        async def achat(self, messages):
            return self.chat(messages)

    llm_client = MockLLMClient()

    # 执行提示链
    result = await chain.run("测试任务", llm_client)

    # 验证结果
    runner.log_result(
        "提示链执行状态",
        result.success,
        True,
        result.success,
        f"执行时间: {result.execution_time:.2f}秒",
    )

    runner.log_result(
        "提示链步骤数量",
        len(result.context.history) == 3,
        3,
        len(result.context.history),
        f"步骤: {[h['step'] for h in result.context.history]}",
    )


async def test_chain_with_context(runner: LiveTestRunner):
    """测试提示链上下文共享"""
    print("\n🔗 测试提示链上下文共享")
    print("=" * 50)

    # 创建共享上下文
    context = ChainContext({"project": "nanoagent", "goal": "测试"})

    # 创建提示链
    chain = PromptChain(
        [
            ChainStep("步骤1", "分析项目 {project}"),
            ChainStep("步骤2", "基于步骤1结果继续"),
        ]
    )

    # Mock LLM 客户端
    class MockLLMClient:
        def chat(self, messages):
            content = messages[0]["content"]
            if "步骤1" in content:
                return "步骤1完成，项目是 nanoagent"
            elif "步骤2" in content:
                return "步骤2完成，基于步骤1"
            return "未知步骤"

        async def achat(self, messages):
            return self.chat(messages)

    llm_client = MockLLMClient()

    # 执行提示链
    await chain.run("测试任务", llm_client, context)

    # 验证上下文数据
    runner.log_result(
        "上下文数据保持",
        context.get("project") == "nanoagent",
        "nanoagent",
        context.get("project"),
        f"上下文数据: {context.data}",
    )


async def test_router_context_tracking(runner: LiveTestRunner):
    """测试路由上下文跟踪"""
    print("\n🧭 测试路由上下文跟踪")
    print("=" * 50)

    router = Router("context_router", default_target="default")

    router.add_route("数据库路由", "database", "数据库").add_route(
        "搜索路由", "search", "搜索"
    )

    # 创建路由上下文
    context = RouteContext({"user_id": "123"})

    # 执行多次路由
    tasks = ["查询数据库", "搜索内容", "查询数据库"]
    for task in tasks:
        await router.route(task, context)

    # 验证历史记录
    runner.log_result(
        "路由历史记录",
        len(context.history) == 3,
        3,
        len(context.history),
        f"历史: {[(h['task'], h['decision']['target']) for h in context.history]}",
    )

    runner.log_result(
        "上下文用户数据保持",
        context.get("user_id") == "123",
        "123",
        context.get("user_id"),
    )


async def test_complex_scenario(runner: LiveTestRunner):
    """测试复杂场景"""
    print("\n🎯 测试复杂场景")
    print("=" * 50)

    # 场景：电商系统智能路由
    router = Router("ecommerce_router", default_target="general")

    router.add_route("商品路由", "product", "商品", priority=5).add_route(
        "订单路由", "order", "订单", priority=5
    ).add_route("用户路由", "user", "用户", priority=5).add_route(
        "支付路由", "payment", "支付", priority=10
    ).add_route("搜索路由", "search", "搜索", priority=3)

    # 添加购物车相关的路由
    router.add_route("购物车路由", "product", "购物车", priority=5)

    # 复杂请求序列
    requests = [
        ("用户登录", "user"),
        ("搜索商品", "product"),  # 搜索应该路由到商品（包含商品关键词）
        ("查看商品详情", "product"),
        ("添加到购物车", "product"),
        ("创建订单", "order"),
        ("支付订单", "payment"),
        ("查看订单状态", "order"),
    ]

    all_passed = True
    for request, expected_target in requests:
        decision = await router.route(request)
        if decision.target != expected_target:
            all_passed = False
            print(f"  ⚠️ {request} -> {decision.target} (期望: {expected_target})")

    runner.log_result(
        "电商系统完整流程",
        all_passed,
        True,
        all_passed,
        f"处理了 {len(requests)} 个请求",
    )


async def test_error_handling(runner: LiveTestRunner):
    """测试错误处理"""
    print("\n🛡️ 测试错误处理")
    print("=" * 50)

    # 测试路由器的默认路由
    router = Router("error_router", default_target="fallback")

    router.add_route("数据库路由", "database", "数据库")

    # 测试没有匹配的路由
    decision = await router.route("不匹配的任务")

    runner.log_result(
        "默认路由回退",
        decision.target == "fallback",
        "fallback",
        decision.target,
        decision.reasoning,
    )

    # 测试提示链错误处理
    def error_step(context):
        raise ValueError("模拟错误")

    chain = PromptChain(
        [
            ChainStep("正常步骤", "正常提示"),
            ChainStep("错误步骤", "错误提示", handler=error_step),
        ],
        stop_on_error=False,
    )

    class MockLLMClient:
        def chat(self, messages):
            return "正常响应"

        async def achat(self, messages):
            return self.chat(messages)

    result = await chain.run("测试错误处理", MockLLMClient())

    runner.log_result(
        "提示链错误处理",
        not result.success and result.error is not None,
        "失败",
        "成功" if result.success else "失败",
        f"错误信息: {result.error}",
    )


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始实时测试")
    print("=" * 50)

    runner = LiveTestRunner()

    # 运行所有测试
    await test_router_functionality(runner)
    await test_router_with_priority(runner)
    await test_chain_functionality(runner)
    await test_chain_with_context(runner)
    await test_router_context_tracking(runner)
    await test_complex_scenario(runner)
    await test_error_handling(runner)

    # 打印摘要
    runner.print_summary()

    # 保存结果
    with open("/home/lora/repos/nanoagent/tests/live_test_results.json", "w") as f:
        json.dump(
            {
                "summary": {
                    "total": runner.passed + runner.failed,
                    "passed": runner.passed,
                    "failed": runner.failed,
                },
                "results": runner.results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\n📁 测试结果已保存到: tests/live_test_results.json")

    return runner.failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
