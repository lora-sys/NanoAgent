"""NanoAgent - 极简 Agent 框架"""

import json
from typing import Any, Dict, List, Tuple, Callable, Optional

from core.spec import TaskSpec
from llm.client import NanoLLMClient
from tools.registry import get_tool_registry


class NanoAgent:
    """极简 Agent 框架 - 零魔法，高性能"""

    def __init__(
        self,
        llm_client: Optional[NanoLLMClient] = None,
        tool_registry: Optional[Any] = None,
    ):
        """
        初始化 Agent

        Args:
            llm_client: LLM 客户端，默认自动创建
            tool_registry: 工具注册表，默认自动创建
        """
        self.llm = llm_client or NanoLLMClient()
        self.tools = tool_registry or get_tool_registry()
        self.spec: Optional[TaskSpec] = None
        self.conversation: List[Dict[str, str]] = []
        self._stop_condition: Optional[Callable[[], bool]] = None

    def run(
        self,
        task: str,
        max_iterations: Optional[int] = None,
        stop_condition: Optional[Callable[[], bool]] = None,
    ) -> Dict[str, Any]:
        """
        执行任务

        Args:
            task: 任务描述
            max_iterations: 最大迭代次数（可选，默认无限制）
            stop_condition: 停止条件函数（可选）

        Returns:
            任务执行结果
        """
        # 初始化任务跟踪
        self.spec = TaskSpec(task)
        self._stop_condition = stop_condition

        # 初始化对话
        self.conversation = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": task},
        ]

        print("🤖 NanoAgent - 极简 Agent 框架")
        print(f"📋 任务: {task}")

        # 主循环 - 无限制，直到条件满足
        iteration = 0
        while True:
            iteration += 1

            # 检查停止条件
            if max_iterations and iteration > max_iterations:
                self.spec.fail(f"达到最大迭代次数 ({max_iterations})")
                break

            if self._stop_condition and self._stop_condition():
                self.spec.complete()
                break

            # 调用 LLM
            try:
                assistant_response = self.llm.chat(self.conversation)
            except Exception as e:
                self.spec.add_error(f"LLM 错误: {e}")
                self.spec.fail(f"LLM 调用失败: {e}")
                break

            # 保存 assistant 响应到对话
            self.conversation.append(
                {"role": "assistant", "content": assistant_response}
            )

            # 提取工具调用
            tool_invocations = self._extract_tool_invocations(assistant_response)

            if not tool_invocations:
                # 没有工具调用，任务完成
                print(f"\n🤖 {assistant_response}")
                self.spec.complete()
                break

            # 执行工具调用
            for tool_name, args in tool_invocations:
                print(f"\n🔧 {tool_name}({args})")
                self.spec.add_tool_call(tool_name)

                try:
                    result = self.tools.execute(tool_name, args)
                    print(f"👁️ {result}")

                    # 记录产物
                    if isinstance(result, dict) and "file_path" in result:
                        # 将绝对路径转换为相对路径
                        file_path = result["file_path"]
                        try:
                            from pathlib import Path

                            cwd = Path.cwd()
                            abs_path = Path(file_path).resolve()
                            if abs_path.is_relative_to(cwd):
                                rel_path = abs_path.relative_to(cwd)
                                self.spec.add_artifact(str(rel_path))
                            else:
                                self.spec.add_artifact(file_path)
                        except Exception:
                            # 转换失败，使用原始路径
                            self.spec.add_artifact(file_path)

                    # 将结果添加到对话
                    self.conversation.append(
                        {
                            "role": "user",
                            "content": f"tool_result({json.dumps(result, ensure_ascii=False)})",
                        }
                    )
                except Exception as e:
                    error_msg = f"工具执行失败: {e}"
                    print(f"❌ {error_msg}")
                    self.spec.add_error(error_msg)
                    self.conversation.append(
                        {
                            "role": "user",
                            "content": f"tool_result({json.dumps({'error': error_msg}, ensure_ascii=False)})",
                        }
                    )

        # 保存任务规范
        spec_file = self.spec.save()
        print(f"\n💾 任务规范: {spec_file}")

        return {
            "status": self.spec.status,
            "iterations": iteration,
            "tools_used": self.spec.tools_used,
            "artifacts": self.spec.artifacts,
            "spec_file": spec_file,
        }

    def chat(self, max_iterations: Optional[int] = None):
        """交互式对话模式"""
        print("🤖 NanoAgent - 极简 Agent 框架")

        # 初始化对话
        self.conversation = [{"role": "system", "content": self._get_system_prompt()}]

        while True:
            # 获取用户输入
            try:
                user_input = input("\n👤 你: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n👋 再见！")
                break

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "退出"):
                print("👋 再见！")
                break

            # 添加用户输入到对话
            self.conversation.append({"role": "user", "content": user_input})

            # 处理任务
            iteration = 0
            while True:
                iteration += 1

                # 检查迭代限制
                if max_iterations and iteration > max_iterations:
                    print("\n⚠️ 达到最大迭代次数")
                    break

                # 调用 LLM
                try:
                    assistant_response = self.llm.chat(self.conversation)
                except Exception as e:
                    print(f"\n❌ LLM 错误: {e}")
                    break

                # 提取工具调用
                tool_invocations = self._extract_tool_invocations(assistant_response)

                if not tool_invocations:
                    # 没有工具调用，显示响应
                    print(f"\n🤖 助手: {assistant_response}")
                    self.conversation.append(
                        {"role": "assistant", "content": assistant_response}
                    )
                    break

                # 执行工具调用
                for tool_name, args in tool_invocations:
                    print(f"\n🔧 {tool_name}({args})")
                    try:
                        result = self.tools.execute(tool_name, args)
                        print(f"👁️ {result}")
                        self.conversation.append(
                            {
                                "role": "user",
                                "content": f"tool_result({json.dumps(result, ensure_ascii=False)})",
                            }
                        )
                    except Exception as e:
                        error_msg = f"工具执行失败: {e}"
                        print(f"❌ {error_msg}")
                        self.conversation.append(
                            {
                                "role": "user",
                                "content": f"tool_result({json.dumps({'error': error_msg}, ensure_ascii=False)})",
                            }
                        )

    def _extract_tool_invocations(self, text: str) -> List[Tuple[str, Dict[str, Any]]]:
        """从文本中提取工具调用"""
        invocations = []
        for line in text.splitlines():
            line = line.strip()
            if not line.startswith("tool:"):
                continue

            try:
                after = line[len("tool:") :].strip()
                name, rest = after.split("(", 1)
                name = name.strip()

                if not rest.endswith(")"):
                    raise ValueError("工具调用格式错误: 缺少右括号")

                json_str = rest[:-1].strip()
                args = json.loads(json_str)
                invocations.append((name, args))
            except Exception as e:
                # 记录解析错误，但不中断整个流程
                error_invocation = (
                    "__parse_error__",
                    {"original_line": line, "error": str(e)},
                )
                invocations.append(error_invocation)

        return invocations

    def _get_system_prompt(self) -> str:
        """生成系统提示"""
        tool_list = self.tools.get_tool_list()

        tool_descriptions = []
        for tool in tool_list:
            func = tool["function"]
            tool_descriptions.append(
                f"工具名: {func['name']}\n"
                f"描述: {func['description']}\n"
                f"参数: {json.dumps(func['parameters'], ensure_ascii=False, indent=2)}\n"
            )

        return (
            "你是一个通用智能助手，帮助用户完成各种任务。\n\n"
            "你有以下工具可以使用：\n\n" + "\n".join(tool_descriptions) + "\n"
            "当你需要使用工具时，请严格按照以下格式输出（必须独占一行）：\n"
            "tool: 工具名({JSON参数})\n\n"
            "例如：\n"
            'tool: read_file({"filename": "README.md"})\n'
            'tool: list_files({"path": "."})\n'
            'tool: edit_file({"path": "test.txt", "old_str": "hello", "new_str": "world"})\n'
            'tool: run_bash({"command": "ls -la"})\n\n'
            "重要规则：\n"
            "1. 工具调用必须独占一行，格式严格为: tool: 名称({JSON})\n"
            "2. JSON 必须是单行格式，使用双引号\n"
            "3. 一次可以调用多个工具，每个工具一行\n"
            "4. 不需要工具时，直接回复用户即可\n"
            "5. 收到工具结果后，继续执行任务\n"
            "6. 直接执行任务，不要询问用户确认\n"
        )
