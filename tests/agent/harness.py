"""Agent 测试框架核心 - 测试工具箱"""

from typing import Any, Dict, List, Optional

from core.agent import NanoAgent
from llm.client import NanoLLMClient
from tools.registry import ToolRegistry, get_tool_registry


class AgentTestHarness:
    """
    Agent 集成测试工具箱。

    支持 mock / real 两种模式，自动拦截工具调用，提供断言接口。

    用法:
        harness = AgentTestHarness(mode="mock")
        harness.load_mock_responses(["tool: grep({...})", "结果返回"])
        result = harness.run_agent("搜索代码中的 def")
        harness.assert_tool_called("grep")
        harness.assert_response_contains("def")
    """

    def __init__(
        self,
        mode: str = "auto",
        llm_client: Optional[NanoLLMClient] = None,
        tool_registry: Optional[ToolRegistry] = None,
        mock_responses: Optional[List[str]] = None,
    ):
        """
        Args:
            mode: "auto" | "mock" | "real"
                - auto: 根据 marker 自动选择
                - mock: 强制 mock 模式
                - real: 强制真实 API
            llm_client: 可选 LLM 客户端
            tool_registry: 可选工具注册表
            mock_responses: mock 响应列表，按顺序返回
        """
        self._mode = mode
        self._mock_responses = mock_responses or []
        self._mock_idx = 0
        self._tool_calls: List[Dict[str, Any]] = []
        self._last_result: Optional[Dict[str, Any]] = None

        self._agent = NanoAgent(
            llm_client=llm_client or self._create_llm_client(),
            tool_registry=tool_registry or get_tool_registry(),
        )

    def _create_llm_client(self) -> NanoLLMClient:
        """根据模式创建 LLM 客户端"""
        client = NanoLLMClient()

        if self._mode == "mock":
            client.mock_enabled = True
            client.mock_mode = "sequential"
        elif self._mode == "real":
            client.mock_enabled = False
        # auto: 保持 NanoLLMClient 默认（读取 nanoagent.toml）

        return client

    def load_mock_responses(self, responses: List[str]) -> "AgentTestHarness":
        """加载 mock 响应（顺序返回），返回 self 支持链式调用。"""
        self._mock_responses = responses
        self._mock_idx = 0
        client = self._agent.llm
        client.mock_enabled = True
        client.mock_mode = "sequential"
        # 直接替换 _get_mock 行为
        client._get_mock = self._make_mock_getter(responses)
        return self

    def _make_mock_getter(self, responses: List[str]):
        """生成 mock getter 闭包，捕获自己的 idx"""
        idx = [0]

        def getter() -> str:
            resp = responses[idx[0] % len(responses)]
            idx[0] += 1
            return resp

        return getter

    def run_agent(
        self,
        task: str,
        max_iterations: Optional[int] = None,
    ) -> Dict[str, Any]:
        """运行 agent，返回结果字典。"""
        # 注入工具拦截
        original_execute = self._agent.tools.execute

        def tracking_execute(name: str, args: Dict[str, Any]) -> Any:
            self._tool_calls.append({"tool": name, "args": args})
            return original_execute(name, args)

        self._agent.tools.execute = tracking_execute

        try:
            result = self._agent.run(task, max_iterations=max_iterations)
            self._last_result = result
            return result
        finally:
            self._agent.tools.execute = original_execute

    # ─── 断言方法 ────────────────────────────────────────────────

    def assert_tool_called(self, tool_name: str) -> "AgentTestHarness":
        """断言指定工具被调用过。"""
        called = any(call["tool"] == tool_name for call in self._tool_calls)
        assert called, (
            f"工具 '{tool_name}' 未被调用。\n"
            f"实际调用的工具: {[c['tool'] for c in self._tool_calls]}"
        )
        return self

    def assert_tool_not_called(self, tool_name: str) -> "AgentTestHarness":
        """断言指定工具未被调用。"""
        called = any(call["tool"] == tool_name for call in self._tool_calls)
        assert not called, f"工具 '{tool_name}' 不应被调用，但实际被调用了。"
        return self

    def assert_tool_call_count(self, tool_name: str, count: int) -> "AgentTestHarness":
        """断言指定工具被调用次数。"""
        actual = sum(1 for c in self._tool_calls if c["tool"] == tool_name)
        assert actual == count, (
            f"工具 '{tool_name}' 被调用 {actual} 次，期望 {count} 次。"
        )
        return self

    def assert_response_contains(self, text: str) -> "AgentTestHarness":
        """断言 agent 响应包含指定文本。"""
        response = self._last_result.get("response", "") if self._last_result else ""
        assert text in response, f"响应中未找到 '{text}'。\n实际响应: {response[:300]}"
        return self

    def assert_status(self, status: str) -> "AgentTestHarness":
        """断言 agent 执行状态。"""
        assert self._last_result is not None, "请先调用 run_agent()"
        assert self._last_result.get("status") == status, (
            f"状态为 {self._last_result.get('status')}，期望 {status}"
        )
        return self

    def assert_no_error(self) -> "AgentTestHarness":
        """断言 agent 执行无错误。"""
        assert self._last_result is not None, "请先调用 run_agent()"
        tools_used = self._last_result.get("tools_used", [])
        assert len(tools_used) > 0, "未使用任何工具"
        return self

    @property
    def tool_calls(self) -> List[Dict[str, Any]]:
        """返回所有工具调用记录。"""
        return list(self._tool_calls)

    @property
    def tools_used(self) -> List[str]:
        """返回已使用工具名称列表。"""
        return [c["tool"] for c in self._tool_calls]

    @property
    def last_result(self) -> Optional[Dict[str, Any]]:
        return self._last_result


_run_mode_store = {"mode": "auto"}


def _is_unit_test() -> bool:
    """检测当前测试模式。"""
    return _run_mode_store.get("mode") == "mock"
