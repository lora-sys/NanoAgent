"""增强功能演示 - 展示门控机制和质量验证"""

import asyncio
from core.router_enhanced import create_customer_service_router
from core.chain_enhanced import (
    EnhancedPromptChain,
    EnhancedChainStep,
    EnhancedChainContext,
    GateResult,
    QualityCheck,
    create_document_creation_chain,
    create_marketing_chain,
)


class MockLLMClient:
    """Mock LLM 客户端用于演示"""

    def chat(self, messages):
        content = messages[0]["content"]

        # 路由测试
        if "退款" in content:
            return '{"target": "refund_service", "reasoning": "用户要求退款", "confidence": 0.95, "complexity": "low"}'
        elif "技术" in content:
            return '{"target": "technical_support", "reasoning": "技术问题", "confidence": 0.9, "complexity": "medium"}'
        elif "咨询" in content:
            return '{"target": "general_service", "reasoning": "一般咨询", "confidence": 0.85, "complexity": "low"}'

        # 提示链测试
        if "创建提纲" in content:
            return """# 文档提纲

## 1. 引言
- 项目背景
- 目标和范围

## 2. 技术架构
- 系统设计
- 技术选型

## 3. 实施方案
- 开发计划
- 测试策略

## 4. 总结
- 预期成果
- 风险评估"""
        elif "检查提纲" in content:
            return "提纲结构完整，覆盖了主要方面，可以继续撰写内容。"
        elif "撰写内容" in content:
            return """# 项目文档

## 1. 引言

本项目旨在开发一个现代化的Web应用系统，提供高效的用户体验和强大的功能支持。

## 2. 技术架构

系统采用微服务架构，使用Python和FastAPI作为后端框架，Vue.js作为前端框架。数据库采用PostgreSQL，缓存使用Redis。

## 3. 实施方案

开发计划分为三个阶段：需求分析、系统设计、开发测试。每个阶段都有明确的里程碑和验收标准。

## 4. 总结

预期项目将在6个月内完成，主要风险包括技术选型和团队协作，已制定相应的应对策略。"""
        elif "翻译" in content:
            return "This project aims to develop a modern web application system..."
        elif "营销文案" in content:
            return "🎉 限时优惠！立即购买享受5折优惠！不要错过这个绝佳机会！"

        return "通用回复"

    async def achat(self, messages):
        return self.chat(messages)


async def demo_enhanced_router():
    """演示增强路由器"""
    print("🎯 增强路由器演示")
    print("=" * 50)

    # 创建客户服务路由器
    router = create_customer_service_router()
    router.set_llm_client(MockLLMClient())

    # 注册不同模型（模拟）
    router.register_model("haiku", MockLLMClient())  # 小模型
    router.register_model("sonnet", MockLLMClient())  # 中等模型
    router.register_model("opus", MockLLMClient())  # 大模型

    # 测试不同类型的请求
    requests = [
        "我要退款，订单号12345",
        "系统出现bug，无法登录",
        "咨询产品价格",
    ]

    for request in requests:
        decision = await router.route(request)
        print(f"请求: {request}")
        print(f"  → 路由到: {decision.target}")
        print(f"  → 原因: {decision.reasoning}")
        print(f"  → 置信度: {decision.confidence}")

        # 获取对应的模型
        router.get_model_for_decision(decision)
        model_pref = decision.metadata.get("model_preference", "default")
        print(f"  → 使用模型: {model_pref}")
        print()


async def demo_enhanced_chain_with_gates():
    """演示带门控机制的提示链"""
    print("🔗 带门控机制的提示链示例")
    print("=" * 50)

    # 创建文档创建链
    chain = create_document_creation_chain()

    # 创建上下文
    context = EnhancedChainContext({"topic": "Web应用开发"})

    # 执行提示链
    result = await chain.run("创建Web应用开发文档", MockLLMClient(), context)

    print(f"✅ 执行状态: {result['success']}")
    print(f"⏱️ 执行时间: {result['execution_time']:.2f}秒")
    print(f"📋 执行步骤数: {result['steps_executed']}")
    print(f"🚪 门控失败: {result['gate_failed']}")
    print(f"📊 质量检查失败: {result['quality_failed']}")
    print()

    # 显示门控和质量检查结果
    if result["context"]["gate_results"]:
        print("🚪 门控检查结果:")
        for i, gate_result in enumerate(result["context"]["gate_results"], 1):
            print(
                f"  {i}. {'通过' if gate_result['passed'] else '失败'}: {gate_result['message']}"
            )
        print()

    if result["context"]["quality_checks"]:
        print("📊 质量检查结果:")
        for i, quality_check in enumerate(result["context"]["quality_checks"], 1):
            print(
                f"  {i}. 分数: {quality_check['score']:.2f} - {'通过' if quality_check['passed'] else '失败'}"
            )
            if quality_check["issues"]:
                print(f"     问题: {', '.join(quality_check['issues'])}")
            if quality_check["suggestions"]:
                print(f"     建议: {', '.join(quality_check['suggestions'])}")
        print()


async def demo_custom_chain_with_validation():
    """演示带自定义验证的提示链"""
    print("🔗 自定义验证提示链示例")
    print("=" * 50)

    # 自定义门控检查
    def check_length_gate(content: str) -> GateResult:
        """检查内容长度"""
        if len(content) < 30:
            return GateResult(
                passed=False,
                message=f"内容太短（{len(content)}字符），至少需要30字符",
                metadata={"length": len(content)},
            )
        return GateResult(
            passed=True,
            message="内容长度符合要求",
            metadata={"length": len(content)},
        )

    # 自定义质量检查
    def check_content_quality(content: str) -> QualityCheck:
        """检查内容质量"""
        issues = []
        suggestions = []

        if len(content) < 50:
            issues.append("内容过于简短")

        if not any(char in content for char in "。！？.!?"):
            issues.append("缺少句子结束标点")
            suggestions.append("添加适当的标点符号")

        score = 1.0 - (len(issues) * 0.3)
        score = max(0.0, min(1.0, score))

        return QualityCheck(
            score=score,
            passed=score >= 0.7,
            issues=issues,
            suggestions=suggestions,
        )

    # 创建自定义提示链
    chain = EnhancedPromptChain(
        [
            EnhancedChainStep(
                name="生成内容",
                prompt="生成一段关于AI的介绍",
                gate_check=check_length_gate,
                quality_check=check_content_quality,
                retry_on_fail=True,
                max_retries=2,
            ),
            EnhancedChainStep(
                name="优化内容",
                prompt="优化生成的内容，使其更加流畅和专业",
            ),
        ],
        name="custom_chain",
        stop_on_gate_fail=True,
        stop_on_quality_fail=False,
    )

    # 执行提示链
    result = await chain.run("AI介绍", MockLLMClient())

    print(f"✅ 执行状态: {result['success']}")
    print(f"📋 执行步骤数: {result['steps_executed']}")

    # 显示执行历史
    print("\n📝 执行历史:")
    for i, history in enumerate(result["context"]["history"], 1):
        print(f"  步骤{i}: {history['step']}")
        if history["gate_result"]:
            gate = history["gate_result"]
            print(
                f"    门控: {'通过' if gate['passed'] else '失败'} - {gate['message']}"
            )

        result_preview = str(history["result"])[:100]
        print(f"    结果: {result_preview}...")
    print()


async def demo_marketing_chain():
    """演示营销内容链"""
    print("🎯 营销内容链示例")
    print("=" * 50)

    # 创建营销内容链
    chain = create_marketing_chain()

    # 执行提示链
    result = await chain.run("为新产品生成营销文案", MockLLMClient())

    print(f"✅ 执行状态: {result['success']}")
    print(f"📋 执行步骤数: {result['steps_executed']}")

    # 显示质量检查结果
    if result["context"]["quality_checks"]:
        print("\n📊 质量检查结果:")
        for i, quality_check in enumerate(result["context"]["quality_checks"], 1):
            print(f"  步骤{i} 质量分数: {quality_check['score']:.2f}")
            if quality_check["suggestions"]:
                print(f"  建议: {', '.join(quality_check['suggestions'])}")
    print()


async def main():
    """主函数"""
    print("🚀 增强功能演示")
    print("=" * 50)
    print()

    await demo_enhanced_router()
    await demo_enhanced_chain_with_gates()
    await demo_custom_chain_with_validation()
    await demo_marketing_chain()

    print("=" * 50)
    print("🎉 所有演示完成！")
    print()
    print("💡 增强功能总结:")
    print("  🚪 门控机制：在路由和执行过程中添加验证检查")
    print("  📊 质量验证：检查每个步骤的输出质量")
    print("  🔄 自动重试：失败的步骤可以自动重试")
    print("  🎯 多模型路由：根据任务复杂度选择不同模型")
    print("  ⚙️ 灵活配置：可自定义各种检查和验证逻辑")


if __name__ == "__main__":
    asyncio.run(main())
