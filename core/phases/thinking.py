"""
Think 阶段处理器

负责分析当前状态并决定下一步行动
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from loguru import logger
import json
import re

from .base import BasePhase
from core.prompt import SYSTEM_PROMPT, REACT_THINK_PROMPT


class ThinkAction(BaseModel):
    """思考阶段的结构化输出"""

    action: str = Field(
        ..., description="动作类型: tool_call, complete, wait, stage_complete, continue"
    )
    tool: Optional[str] = Field(
        default=None, description="工具名称（当 action=tool_call 时必须）"
    )
    arguments: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="工具参数（当 action=tool_call 时必须）"
    )
    reason: Optional[str] = Field(default=None, description="动作原因说明")


class ThinkingPhase(BasePhase):
    """Think 阶段处理器"""

    def execute(
        self,
        task: str,
        context: Dict,
        observations: list,
        step_count: int = 0,
        spec: Any = None,
        state: Any = None,
    ) -> Dict[str, Any]:
        """
        执行 Think 阶段

        Args:
            task: 用户任务
            context: 上下文字典
            observations: 历史观察
            step_count: 当前步数
            spec: 任务规范
            state: Agent 状态管理器

        Returns:
            思考结果（包含 action 和参数）
        """
        logger.info(f"=== Think Phase (Step {step_count + 1}) ===")

        if context is None:
            context = {}

        # 构建 prompt
        prompt = self._build_prompt(
            task=task,
            context=context,
            observations=observations,
            step_count=step_count,
            spec=spec,
            state=state,
        )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        try:
            # 使用结构化输出
            think_result = self.llm_client.structured_chat(
                messages, ThinkAction, temperature=0.7
            )

            logger.info(f"Structured think succeeded: {think_result.action}")

            return {
                "action": think_result.action,
                "tool": think_result.tool,
                "arguments": think_result.arguments or {},
                "thought": think_result.reason or "",
            }

        except Exception as e:
            logger.warning(
                f"Structured think failed, falling back to tool calling: {e}"
            )
            return self._think_with_tool_calling(messages)

    def _build_prompt(
        self,
        task: str,
        context: Dict,
        observations: list,
        step_count: int,
        spec: Any,
        state: Any,
    ) -> str:
        """构建动态 prompt"""
        # 获取需求信息摘要
        requirements_summary = ""
        if state:
            requirements_summary = state.get_requirements_summary()

        # 检查需求确认状态
        requirements_confirmed = False
        current_state = "initial"
        if state:
            requirements_confirmed = state.is_requirements_confirmed()
            current_state = state.get_current_state().value

        # 获取最近观察
        recent_observations = self._get_recent_observations(observations, max_items=3)

        # 构建 prompt
        prompt = REACT_THINK_PROMPT.format(
            current_step=step_count + 1,
            completed_steps=[s.get("step", 0) for s in observations],
            step_count=step_count,
            max_steps=getattr(self, "max_steps", 20),
            task_goal=spec.overall_goal if spec else task,
            recent_observations=recent_observations,
            requirements=requirements_summary,
            available_tools=self.tool_registry.get_tool_descriptions()
            if self.tool_registry
            else "No tools available",
        )

        # 需求已确认时添加强制提示
        if requirements_confirmed:
            prompt += "\n\n【重要提示】\n"
            prompt += f"需求已确认！当前状态: {current_state}\n"
            prompt += "不要再向用户询问需求问题！\n"
            prompt += "必须开始执行任务，创建交付物！\n"
            prompt += "使用 write_file 或 safe_write_file 工具创建文件。\n"
            prompt += "不要使用 ask_user_question 工具！\n"
            logger.info("需求已确认，添加强制提示防止重复询问")

        # 添加当前阶段约束
        if context.get("current_stage_spec"):
            prompt += "\n\n【当前阶段约束】\n"
            prompt += context["current_stage_spec"]

        if context.get("constraints"):
            constraints = context["constraints"]
            if isinstance(constraints, list):
                constraints = {"always": constraints, "never": []}
            elif not isinstance(constraints, dict):
                constraints = {}

            if constraints.get("never"):
                prompt += "\n【禁止操作】\n"
                for c in constraints["never"]:
                    prompt += f"- {c}\n"

        return prompt

    def _think_with_tool_calling(self, messages: list) -> Dict[str, Any]:
        """回退：使用 Tool Calling API"""
        if not self.tool_registry:
            return self._parse_think_fallback("")

        tool_schemas = self.tool_registry.get_tool_schemas()

        response = self.llm_client.tool_chat(
            messages, tools=tool_schemas, temperature=0.7
        )

        # 检查是否有工具调用
        if response.get("tool_calls"):
            tool_call = response["tool_calls"][0]
            tool_name = tool_call["function"]["name"]
            try:
                arguments = json.loads(tool_call["function"]["arguments"])
            except json.JSONDecodeError:
                arguments = {}

            logger.info(f"Tool call parsed via native API: {tool_name}")
            return {
                "action": "tool_call",
                "tool": tool_name,
                "arguments": arguments,
                "thought": response.get("content", ""),
            }

        # 回退到文本解析
        content = response.get("content", "")
        return self._parse_think_fallback(content)

    def _parse_think_fallback(self, response: str) -> Dict[str, Any]:
        """回退解析：从文本中提取工具调用信息"""
        # 尝试从 markdown 代码块中提取 JSON
        code_block_match = re.search(r"```json\s*\n(.*?)\n\s*```", response, re.DOTALL)
        if code_block_match:
            try:
                json_str = code_block_match.group(1)
                action_data = json.loads(json_str)

                tool_name = action_data.get("tool") or action_data.get(
                    "function", "unknown"
                )
                arguments = action_data.get(
                    "arguments", action_data.get("parameters", {})
                )

                return {
                    "action": "tool_call",
                    "tool": tool_name,
                    "arguments": arguments,
                    "thought": response[:200],
                }
            except Exception:
                pass

        # 尝试正则提取工具名
        tool_name = "unknown"
        tool_match = re.search(r'"tool"\s*:\s*"([^"]+)"', response)
        if tool_match:
            tool_name = tool_match.group(1)

        return {
            "action": "tool_call",
            "tool": tool_name,
            "arguments": {},
            "thought": response[:200],
        }
