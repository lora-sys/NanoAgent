"""提示链实际应用示例 - 展示真实场景中的使用方法"""

import asyncio
from core.chain import PromptChain, ChainStep, ChainContext


class MockLLMClient:
    """Mock LLM 客户端用于演示"""

    def chat(self, messages):
        content = messages[0]["content"]

        # 代码审查场景
        if "代码质量分析" in content:
            return """代码质量分析结果：
- 代码结构清晰，模块划分合理
- 缺少错误处理机制
- 部分函数过长，建议重构
- 缺少单元测试覆盖
- 命名规范良好"""

        elif "性能评估" in content:
            return """性能评估结果：
- 时间复杂度：O(n²)，存在优化空间
- 内存使用：合理，无明显泄漏
- 数据库查询：存在 N+1 问题
- 缓存策略：建议添加缓存层
- 并发处理：当前为同步模式，可优化为异步"""

        elif "安全审查" in content:
            return """安全审查结果：
- SQL注入风险：已使用参数化查询
- XSS防护：需要添加输入验证
- 认证机制：使用 JWT，实现良好
- 敏感数据：建议加密存储
- 依赖项：存在已知漏洞的依赖"""

        elif "改进建议" in content:
            return """改进建议：
1. 添加错误处理和日志记录
2. 重构长函数，提高可读性
3. 添加单元测试，提高覆盖率
4. 优化数据库查询，解决 N+1 问题
5. 添加缓存层，提升性能
6. 实现异步处理，提高并发能力
7. 加强输入验证，防止 XSS 攻击
8. 加密敏感数据，提高安全性"""

        # 项目架构分析场景
        elif "项目概览" in content:
            return """项目概览：
- 项目名称：电商系统
- 技术栈：Python + FastAPI + PostgreSQL
- 架构模式：分层架构
- 核心模块：用户、商品、订单、支付
- 部署方式：Docker + Kubernetes"""

        elif "模块依赖" in content:
            return """模块依赖关系：
- 用户模块：被订单、支付模块依赖
- 商品模块：被订单模块依赖
- 订单模块：依赖用户、商品、支付模块
- 支付模块：依赖用户、订单模块
- 数据库：所有模块共享"""

        elif "数据流分析" in content:
            return """数据流分析：
1. 用户浏览商品 → 商品模块
2. 用户下单 → 订单模块 → 库存检查
3. 支付处理 → 支付模块 → 订单更新
4. 订单完成 → 通知用户 → 用户模块
5. 数据同步 → 数据库 → 分析模块"""

        elif "架构优化建议" in content:
            return """架构优化建议：
1. 引入消息队列，解耦模块依赖
2. 实现微服务架构，提高扩展性
3. 添加 API 网关，统一接口管理
4. 实现读写分离，优化数据库性能
5. 添加监控和日志系统
6. 实现自动化测试和部署"""

        return "分析完成"

    async def achat(self, messages):
        return self.chat(messages)


async def demo_code_review():
    """演示代码审查场景"""
    print("🎯 场景1：代码审查")
    print("=" * 50)

    # 创建代码审查提示链
    chain = PromptChain(
        [
            ChainStep(
                "代码质量分析",
                "对以下代码进行质量分析，包括代码结构、可读性、错误处理等方面",
            ),
            ChainStep(
                "性能评估", "评估代码的性能表现，包括时间复杂度、内存使用、数据库查询等"
            ),
            ChainStep(
                "安全审查", "检查代码的安全问题，包括注入攻击、认证授权、数据加密等"
            ),
            ChainStep("改进建议", "基于以上分析，提供具体的改进建议和实施方案"),
        ]
    )

    client = MockLLMClient()
    result = await chain.run("审查以下代码的质量、性能和安全性", client)

    print("✅ 审查完成")
    print(f"⏱️ 执行时间: {result.execution_time:.2f}秒")
    print(f"📊 分析步骤: {len(result.context.history)} 个")
    print("\n📋 审查摘要:")
    for i, history in enumerate(result.context.history, 1):
        print(f"\n步骤{i} - {history['step']}:")
        print(f"  {history['result'][:100]}...")
    print()


async def demo_project_analysis():
    """演示项目架构分析场景"""
    print("🎯 场景2：项目架构分析")
    print("=" * 50)

    # 创建项目分析提示链
    chain = PromptChain(
        [
            ChainStep("项目概览", "分析项目的整体结构、技术栈和核心功能"),
            ChainStep("模块依赖", "梳理各模块之间的依赖关系和耦合度"),
            ChainStep("数据流分析", "分析系统中的数据流动路径和处理流程"),
            ChainStep("架构优化建议", "基于分析结果，提供架构优化建议"),
        ]
    )

    client = MockLLMClient()
    result = await chain.run("分析电商系统的架构设计", client)

    print("✅ 分析完成")
    print(f"⏱️ 执行时间: {result.execution_time:.2f}秒")
    print(f"📊 分析步骤: {len(result.context.history)} 个")
    print("\n📋 分析摘要:")
    for i, history in enumerate(result.context.history, 1):
        print(f"\n步骤{i} - {history['step']}:")
        print(f"  {history['result'][:100]}...")
    print()


async def demo_custom_analysis_with_context():
    """演示带上下文的自定义分析"""
    print("🎯 场景3：带上下文的自定义分析")
    print("=" * 50)

    # 创建共享上下文
    context = ChainContext(
        {
            "project_type": "Web应用",
            "tech_stack": "Python + FastAPI",
            "team_size": "5人",
            "deadline": "3个月",
        }
    )

    # 创建带上下文的提示链
    chain = PromptChain(
        [
            ChainStep(
                "需求分析",
                "分析项目需求，考虑项目类型：{project_type}，技术栈：{tech_stack}",
            ),
            ChainStep(
                "技术方案设计",
                "设计技术方案，考虑团队规模：{team_size}，截止日期：{deadline}",
            ),
            ChainStep("实施计划", "制定详细的实施计划，分配任务和时间"),
        ]
    )

    client = MockLLMClient()
    result = await chain.run("为新项目制定开发计划", client, context)

    print("✅ 计划制定完成")
    print(f"⏱️ 执行时间: {result.execution_time:.2f}秒")
    print(f"📊 上下文数据: {result.context.data}")
    print()


async def demo_error_recovery():
    """演示错误恢复机制"""
    print("🎯 场景4：错误恢复机制")
    print("=" * 50)

    def unreliable_step(context):
        """模拟可能失败的步骤"""
        import random

        if random.random() < 0.3:  # 30% 概率失败
            raise RuntimeError("模拟网络错误")
        return "步骤执行成功"

    chain = PromptChain(
        [
            ChainStep("可靠步骤1", "这是一个可靠的步骤"),
            ChainStep("不可靠步骤", "这个步骤可能失败", handler=unreliable_step),
            ChainStep("可靠步骤2", "这是一个可靠的步骤"),
        ],
        stop_on_error=False,
    )  # 错误时继续

    client = MockLLMClient()
    result = await chain.run("测试错误恢复机制", client)

    print(f"✅ 执行状态: {result.success}")
    print(f"📊 执行步骤: {len(result.context.history)} 个")
    if result.error:
        print(f"⚠️ 错误信息: {result.error}")
    print()


async def demo_parallel_analysis():
    """演示并行分析场景"""
    print("🎯 场景5：并行分析")
    print("=" * 50)

    # 创建并行分析链
    chain = PromptChain(
        [
            ChainStep("前端分析", "分析前端代码结构和性能"),
            ChainStep("后端分析", "分析后端API设计和性能"),
            ChainStep("数据库分析", "分析数据库设计和查询性能"),
            ChainStep("综合评估", "综合以上分析，给出整体评估"),
        ]
    )

    client = MockLLMClient()
    result = await chain.run("分析全栈应用的性能", client)

    print("✅ 分析完成")
    print(f"⏱️ 执行时间: {result.execution_time:.2f}秒")
    print(f"📊 分析维度: {len(result.context.history)} 个")
    print()


async def main():
    """主函数"""
    print("🚀 提示链实际应用示例")
    print("=" * 50)
    print()

    await demo_code_review()
    await demo_project_analysis()
    await demo_custom_analysis_with_context()
    await demo_error_recovery()
    await demo_parallel_analysis()

    print("=" * 50)
    print("🎉 所有示例演示完成！")
    print()
    print("💡 提示链适用于：")
    print("  - 代码审查和质量分析")
    print("  - 项目架构分析")
    print("  - 复杂任务分解")
    print("  - 多步骤工作流程")
    print("  - 需要上下文共享的场景")
    print("  - 需要错误恢复的任务")


if __name__ == "__main__":
    asyncio.run(main())
