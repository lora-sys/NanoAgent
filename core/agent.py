"""NanoAgent - 精简版 Agent 主循环"""

from typing import Any, Dict
import json

from config import get_config
from core.state import AgentState
from core.template import get_template_manager
from core.marker import MarkerParser
from llm.client import NanoLLMClient
from tools.registry import get_tool_registry


class NanoAgent:
    def __init__(self):
        cfg = get_config()
        self.llm = NanoLLMClient(model=cfg.get("llm", "default.model"))
        self.tools = get_tool_registry()
        self.state = AgentState()
        self.tmpl = get_template_manager()
        self.max_steps = cfg.get("core", "performance.max_steps", 20)

    def run(self, task: str) -> Dict[str, Any]:
        self.state.reset()
        self.state.update_spec({"task": task, "status": "running"})
        self.state.add_message("system", self._system_prompt())
        self.state.add_message("user", task)

        cli = self._get_cli()
        cli.display_header()

        while True:
            self.state.step_count += 1
            if self.state.step_count > self.max_steps:
                cli.display_result(f"达到最大步数 ({self.max_steps})", False)
                break

            response = self._inner_loop(cli)
            if response.get("task_completed"):
                cli.display_result(response.get("content", "任务完成"), True)
                self.state.update_spec({"status": "completed"})
                break

            if response.get("content"):
                cli.display_action("content", response["content"])
                self.state.add_message("assistant", response["content"])

            user_input = cli.display_question(
                "请继续输入你的问题或任务，或输入'exit'退出："
            )
            if user_input.lower() in ("exit", "quit", "退出"):
                self.state.update_spec({"status": "completed"})
                cli.display_result("用户退出", True)
                break

            if user_input.strip():
                self.state.add_message("user", user_input)

        return {
            "status": "completed",
            "steps_executed": self.state.step_count,
            "artifacts": self.state.get_artifacts(),
            "decisions": self.state.get_decisions(),
            "current_stage": self.state.get_current_stage(),
        }

    def _inner_loop(self, cli) -> Dict[str, Any]:
        while True:
            think_result = self._think()

            # 显示思考过程
            if "thinking" in think_result:
                cli.display_marker("THINKING", think_result["thinking"])

            # 显示计划
            if "plan" in think_result:
                cli.display_marker("PLAN", think_result["plan"])

            action = think_result.get("action", "")

            if action == "tool_call" and think_result.get("tool"):
                cli.display_marker(
                    "TOOL", think_result.get("reason", think_result["tool"])
                )
                try:
                    result = self.tools.execute(
                        think_result["tool"], think_result.get("arguments") or {}
                    )
                    cli.display_marker("OBSERVATION", str(result))
                    self.state.add_message("user", f"工具执行结果: {result}")
                except Exception as e:
                    cli.display_marker("OBSERVATION", f"工具执行失败: {e}")
                    self.state.add_message("user", f"工具执行失败: {e}")

                # 显示反思
                if "reflection" in think_result:
                    cli.display_marker("REFLECTION", think_result["reflection"])

                continue

            if action == "complete":
                if "response" in think_result:
                    cli.display_marker("RESPONSE", think_result["response"])
                return {
                    "content": think_result.get("reason", "任务完成"),
                    "task_completed": True,
                }

            if action == "wait":
                if "response" in think_result:
                    cli.display_marker("RESPONSE", think_result["response"])
                return {
                    "content": think_result.get("reason", "等待用户输入"),
                    "should_break": True,
                }

            return {"content": think_result.get("reason", ""), "should_break": True}

    def _think(self) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "你是NanoAgent，使用标记格式输出。"},
            {"role": "user", "content": self._build_think_prompt()},
        ]
        try:
            response = self.llm.chat(messages, temperature=0.7)
            return self._parse_marker_response(response)
        except Exception as e:
            return {"action": "wait", "reason": f"LLM 错误: {e}"}

    def _parse_marker_response(self, response: str) -> Dict[str, Any]:
        """解析标记格式的响应"""
        parser = MarkerParser()
        sections = parser.parse(response)

        # 提取不同类型的标记
        thinking = parser.extract_first("THINKING")
        plan = parser.extract_first("PLAN")
        tool = parser.extract_first("TOOL")
        observation = parser.extract_first("OBSERVATION")
        reflection = parser.extract_first("REFLECTION")
        response_section = parser.extract_first("RESPONSE")

        result = {}

        # 提取工具调用信息
        if tool:
            result["action"] = "tool_call"
            result["tool"] = tool.metadata.get("name", "")
            if "args" in tool.metadata:
                try:
                    result["arguments"] = json.loads(tool.metadata["args"])
                except json.JSONDecodeError:
                    result["arguments"] = {}
            result["reason"] = tool.content

        # 提取响应（完成或等待）
        elif response_section:
            content = response_section.content.lower()
            if "完成" in content or "complete" in content:
                result["action"] = "complete"
                result["reason"] = response_section.content
            else:
                result["action"] = "wait"
                result["reason"] = response_section.content

        # 默认等待
        else:
            result["action"] = "wait"
            result["reason"] = "无法解析响应"

        # 附加思考、计划、观察、反思信息
        if thinking:
            result["thinking"] = thinking.content
        if plan:
            result["plan"] = plan.content
        if observation:
            result["observation"] = observation.content
        if reflection:
            result["reflection"] = reflection.content

        return result

    def _system_prompt(self) -> str:
        return (
            "你是NanoAgent，一个专业的数据驱动智能助手。\n\n"
            "你的职责：\n"
            "1. 理解用户任务，制定清晰的执行计划\n"
            "2. 通过工具调用完成具体操作\n"
            "3. 自动管理spec：记录决策、生成文件、推进阶段\n\n"
            "输出格式（使用标记）：\n"
            "- <|THINKING|>思考过程<|/THINKING|>\n"
            "- <|PLAN|>执行计划<|/PLAN|>\n"
            "- <|TOOL|name=\"工具名\" args='参数JSON'|>工具调用描述<|/TOOL|>\n"
            "- <|OBSERVATION|>观察结果<|/OBSERVATION|>\n"
            "- <|REFLECTION|>反思总结<|/REFLECTION|>\n"
            "- <|RESPONSE|>最终响应<|/RESPONSE|>\n\n"
            "工作原则：\n"
            "- 保持对话简洁，专注于任务执行\n"
            "- 每次重要操作都要使用标记格式\n"
            "- 优先使用工具完成具体操作\n"
            "- 遇到问题时主动寻求用户指导\n\n"
            "开始执行任务吧！"
        )

    def _build_think_prompt(self) -> str:
        tm = self.tmpl
        try:
            return tm.get_think_prompt(
                task_goal=self.state.get_task(),
                current_step=self.state.step_count,
                current_stage=self.state.get_current_stage(),
                artifacts=", ".join(self.state.get_artifacts()[-5:]),
                decisions=", ".join(self.state.get_decisions()[-3:]),
                available_tools=self.tools.get_tool_descriptions(),
            )
        except Exception:
            return (
                f"任务: {self.state.get_task()}\n"
                f"步骤: {self.state.step_count}\n"
                f"当前阶段: {self.state.get_current_stage()}\n"
                f"可用工具:\n{self.tools.get_tool_descriptions()}\n\n"
                "请使用标记格式输出你的思考过程和下一步操作。\n"
                "示例：\n"
                "<|THINKING|>\n"
                "我需要读取文件来完成任务\n"
                "<|/THINKING|>\n\n"
                "<|TOOL|name='read_file' args='{\"path\": \"/test.txt\"}'|>\n"
                "读取文件内容\n"
                "<|/TOOL|>"
            )

    @staticmethod
    def _get_cli():
        import sys
        import os

        class SimpleCLI:
            # 标记类型对应的图标和颜色
            MARKER_STYLES = {
                "THINKING": {"icon": "🧠", "color": "\033[94m"},  # 蓝色
                "PLAN": {"icon": "📋", "color": "\033[93m"},  # 黄色
                "TOOL": {"icon": "🔧", "color": "\033[92m"},  # 绿色
                "OBSERVATION": {"icon": "👁️", "color": "\033[96m"},  # 青色
                "REFLECTION": {"icon": "🤔", "color": "\033[95m"},  # 紫色
                "RESPONSE": {"icon": "💬", "color": "\033[97m"},  # 白色
            }

            @staticmethod
            def display_header():
                print("=" * 60 + "\n🤖 NanoAgent - 智能任务执行系统\n" + "=" * 60)

            @staticmethod
            def display_result(msg: str, ok: bool = True):
                print(f"{'✅' if ok else '❌'} {msg}")

            @staticmethod
            def display_action(atype: str, details: str):
                icon = "🔧" if atype == "tool_call" else "📝"
                print(f"\n{icon} {details[:200]}")

            @staticmethod
            def display_marker(marker_type: str, content: str):
                """美化显示标记内容"""
                style = SimpleCLI.MARKER_STYLES.get(
                    marker_type, {"icon": "📝", "color": "\033[0m"}
                )
                icon = style["icon"]
                color = style["color"]
                reset = "\033[0m"

                print(f"\n{color}{icon} [{marker_type}]{reset}")
                print(f"{color}{'─' * 58}{reset}")
                print(f"{color}{content}{reset}")
                print(f"{color}{'─' * 58}{reset}")

            @staticmethod
            def display_question(q: str, options=None) -> str:
                if not sys.stdin.isatty() or os.environ.get("NANOAGENT_TEST"):
                    return "继续执行"
                print(f"\n🤔 {q}")
                if options:
                    for i, o in enumerate(options, 1):
                        print(f"  {i}. {o}")
                return input("请输入你的回答: ").strip()

        return SimpleCLI()
