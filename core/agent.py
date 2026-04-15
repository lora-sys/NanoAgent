"""NanoAgent - 精简版 Agent 主循环"""

from typing import Any, Dict, Optional

from config import get_config
from core.state import AgentState
from core.template import get_template_manager
from llm.client import NanoLLMClient
from models import ThinkAction
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

            user_input = cli.display_question("请继续输入你的问题或任务，或输入'exit'退出：")
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
            action = think_result.get("action", "")

            if action == "stage_complete":
                self.state.update_stage(think_result.get("next_stage", "unknown"), "completed", think_result.get("arguments"))
                return {"content": "阶段完成", "should_break": True}
            if action == "artifact_added":
                args = think_result.get("arguments") or {}
                self.state.add_artifact(args.get("path", ""), args.get("description", ""))
                return {"content": "文件已生成", "should_break": True}
            if action == "decision_made":
                args = think_result.get("arguments") or {}
                self.state.add_decision(args.get("decision", ""), args.get("rationale", ""))
                return {"content": "决策已记录", "should_break": True}
            if action == "tool_call" and think_result.get("tool"):
                cli.display_action("tool_call", think_result["tool"])
                try:
                    result = self.tools.execute(think_result["tool"], think_result.get("arguments") or {})
                    self.state.add_message("user", f"工具执行结果: {result}")
                except Exception as e:
                    self.state.add_message("user", f"工具执行失败: {e}")
                continue
            if action == "complete":
                return {"content": think_result.get("reason", "任务完成"), "task_completed": True}
            if action == "wait":
                return {"content": think_result.get("reason", "等待用户输入"), "should_break": True}
            return {"content": think_result.get("reason", ""), "should_break": True}

    def _think(self) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "你是NanoAgent，只返回JSON。"},
            {"role": "user", "content": self._build_think_prompt()},
        ]
        try:
            return self.llm.structured_chat(messages, ThinkAction, temperature=0.7).model_dump()
        except Exception as e:
            return {"action": "wait", "reason": f"LLM 错误: {e}"}

    def _system_prompt(self) -> str:
        return (
            "你是NanoAgent，一个专业的数据驱动智能助手。\n\n"
            "你的职责：\n"
            "1. 理解用户任务，制定清晰的执行计划\n"
            "2. 通过工具调用完成具体操作\n"
            "3. 自动管理spec：记录决策、生成文件、推进阶段\n\n"
            "工作原则：\n"
            "- 保持对话简洁，专注于任务执行\n"
            "- 每次重要操作都要更新spec\n"
            "- 优先使用工具完成具体操作\n"
            "- 遇到问题时主动寻求用户指导\n\n"
            "spec操作：\n"
            "- 生成文件：artifact_added\n"
            "- 做出决策：decision_made\n"
            "- 完成阶段：stage_complete\n"
            "- 使用工具：tool_call\n\n"
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
                '请决定下一步操作。返回 JSON: {"action": "tool_call|complete|wait|stage_complete|artifact_added|decision_made", ...}'
            )

    @staticmethod
    def _get_cli():
        import sys, os

        class SimpleCLI:
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
            def display_question(q: str, options=None) -> str:
                if not sys.stdin.isatty() or os.environ.get("NANOAGENT_TEST"):
                    return "继续执行"
                print(f"\n🤔 {q}")
                if options:
                    for i, o in enumerate(options, 1):
                        print(f"  {i}. {o}")
                return input("请输入你的回答: ").strip()

        return SimpleCLI()
