"""测试提示链功能"""

import asyncio
from core.chain import (
    PromptChain,
    ChainStep,
    ChainContext,
    ChainResult,
    create_analysis_chain,
    create_design_chain,
)


def test_chain_context():
    """测试链式上下文"""
    context = ChainContext({"input": "测试输入"})

    # 测试 set 和 get
    context.set("key1", "value1")
    assert context.get("key1") == "value1"
    assert context.get("nonexistent", "default") == "default"

    # 测试 history
    context.add_history("step1", "result1")
    assert len(context.history) == 1
    assert context.history[0]["step"] == "step1"

    # 测试 to_dict
    data_dict = context.to_dict()
    assert "data" in data_dict
    assert "history" in data_dict
    assert "metadata" in data_dict

    print("✅ 链式上下文测试通过")


def test_chain_result():
    """测试链式结果"""
    context = ChainContext()
    result = ChainResult(
        success=True, final_output="最终输出", context=context, error=None
    )
    result.execution_time = 1.5

    # 测试属性
    assert result.success is True
    assert result.final_output == "最终输出"
    assert result.execution_time == 1.5

    # 测试 to_dict
    result_dict = result.to_dict()
    assert result_dict["success"] is True
    assert result_dict["final_output"] == "最终输出"
    assert result_dict["execution_time"] == 1.5

    print("✅ 链式结果测试通过")


def test_chain_step():
    """测试链式步骤"""
    step = ChainStep(name="测试步骤", prompt="这是一个测试提示")

    # 测试属性
    assert step.name == "测试步骤"
    assert step.prompt == "这是一个测试提示"
    assert step.handler is None

    # 测试 _build_llm_input
    context = ChainContext({"key": "value"})
    context.add_history("prev_step", "prev_result")
    llm_input = step._build_llm_input(context)

    assert "这是一个测试提示" in llm_input
    assert "上下文信息" in llm_input
    assert "历史步骤" in llm_input

    print("✅ 链式步骤测试通过")


def test_prompt_chain():
    """测试提示链"""
    chain = PromptChain(
        steps=[
            ChainStep("步骤1", "提示1"),
            ChainStep("步骤2", "提示2"),
            ChainStep("步骤3", "提示3"),
        ],
        name="测试链",
        stop_on_error=True,
    )

    # 测试属性
    assert chain.name == "测试链"
    assert len(chain.steps) == 3
    assert chain.stop_on_error is True

    # 测试 add_step
    new_step = ChainStep("步骤4", "提示4")
    chain.add_step(new_step)
    assert len(chain.steps) == 4

    # 测试 get_step
    found_step = chain.get_step("步骤2")
    assert found_step is not None
    assert found_step.name == "步骤2"

    # 测试 remove_step
    removed = chain.remove_step("步骤3")
    assert removed is True
    assert len(chain.steps) == 3

    # 测试 to_dict
    chain_dict = chain.to_dict()
    assert chain_dict["name"] == "测试链"
    assert len(chain_dict["steps"]) == 3

    print("✅ 提示链测试通过")


async def test_prompt_chain_execution():
    """测试提示链执行"""
    # 创建简单的测试链
    chain = PromptChain(
        [
            ChainStep("步骤1", "请回复：步骤1完成"),
            ChainStep("步骤2", "请回复：步骤2完成"),
        ]
    )

    # 创建 mock LLM 客户端
    class MockLLMClient:
        def chat(self, messages):
            content = messages[0]["content"]
            if "请回复：步骤1完成" in content:
                return "步骤1完成"
            elif "请回复：步骤2完成" in content:
                return "步骤2完成"
            return "未知步骤"

    client = MockLLMClient()

    # 执行提示链
    result = await chain.run("测试输入", client)

    # 验证结果
    assert result.success is True
    assert result.execution_time is not None
    assert len(result.context.history) == 2
    assert result.context.get("步骤1") == "步骤1完成"
    assert result.context.get("步骤2") == "步骤2完成"

    print("✅ 提示链执行测试通过")


def test_prompt_chain_sync():
    """测试提示链同步执行"""
    chain = PromptChain(
        [
            ChainStep("步骤1", "请回复：步骤1完成"),
        ]
    )

    class MockLLMClient:
        def chat(self, messages):
            return "步骤1完成"

    client = MockLLMClient()

    # 同步执行
    result = chain.run_sync("测试输入", client)

    assert result.success is True
    assert result.final_output == "步骤1完成"

    print("✅ 提示链同步执行测试通过")


def test_create_analysis_chain():
    """测试创建分析链"""
    chain = create_analysis_chain()

    assert chain.name == "analysis_chain"
    assert len(chain.steps) == 4
    assert chain.steps[0].name == "分析需求"
    assert chain.steps[1].name == "制定计划"
    assert chain.steps[2].name == "执行分析"
    assert chain.steps[3].name == "总结结果"

    print("✅ 分析链创建测试通过")


def test_create_design_chain():
    """测试创建设计链"""
    chain = create_design_chain()

    assert chain.name == "design_chain"
    assert len(chain.steps) == 4
    assert chain.steps[0].name == "理解需求"
    assert chain.steps[1].name == "设计方案"
    assert chain.steps[2].name == "验证设计"
    assert chain.steps[3].name == "完善方案"

    print("✅ 设计链创建测试通过")


def test_chain_error_handling():
    """测试错误处理"""

    # 创建会出错的步骤
    def error_handler(context):
        raise ValueError("测试错误")

    chain = PromptChain(
        [
            ChainStep("正常步骤", "正常提示"),
            ChainStep("错误步骤", "错误提示", handler=error_handler),
            ChainStep("后续步骤", "后续提示"),
        ],
        stop_on_error=True,
    )

    class MockLLMClient:
        def chat(self, messages):
            return "正常结果"

    client = MockLLMClient()

    # 同步执行
    result = chain.run_sync("测试输入", client)

    # 验证错误处理
    assert result.success is False
    assert result.error is not None
    assert "错误步骤" in result.error
    # 由于 stop_on_error=True，后续步骤不应该执行
    assert len(result.context.history) == 2  # 正常步骤 + 错误步骤

    print("✅ 错误处理测试通过")


def test_chain_continue_on_error():
    """测试错误时继续执行"""

    def error_handler(context):
        raise ValueError("测试错误")

    chain = PromptChain(
        [
            ChainStep("正常步骤", "正常提示"),
            ChainStep("错误步骤", "错误提示", handler=error_handler),
            ChainStep("后续步骤", "后续提示"),
        ],
        stop_on_error=False,
    )

    class MockLLMClient:
        def chat(self, messages):
            return "正常结果"

    client = MockLLMClient()

    # 同步执行
    result = chain.run_sync("测试输入", client)

    # 验证继续执行
    assert result.success is False  # 仍然失败
    assert len(result.context.history) == 3  # 所有步骤都执行了

    print("✅ 错误时继续执行测试通过")


if __name__ == "__main__":
    print("🧪 开始测试提示链功能...")

    test_chain_context()
    test_chain_result()
    test_chain_step()
    test_prompt_chain()

    # 异步测试
    asyncio.run(test_prompt_chain_execution())

    test_prompt_chain_sync()
    test_create_analysis_chain()
    test_create_design_chain()
    test_chain_error_handling()
    test_chain_continue_on_error()

    print("\n🎉 所有测试通过！")
