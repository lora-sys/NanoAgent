"""NanoAgent - 极简 Agent 框架"""

import json
import re
from typing import Any, Dict, List, Tuple, Callable, Optional

from core.spec import TaskSpec
from llm.client import NanoLLMClient
from tools.registry import ToolRegistry, get_tool_registry


class NanoAgent:
    """极简 Agent 框架 - 零魔法，高性能"""

    def __init__(
        self,
        llm_client: Optional[NanoLLMClient] = None,
        tool_registry: Optional[ToolRegistry] = None,
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
        """从文本中提取工具调用，支持 XML 友好的标记格式



        支持两种格式：

        1. 新格式（推荐）：<tool name="xxx" args='{"key":"value"}'/>

        2. 旧格式（兼容）：tool: name({"key":"value"})

        """

        invocations = []

        # 编译正则表达式以提高性能
        xml_pattern = re.compile(r'<tool\s+name="([^"]+)"\s+args=\'([^\']*)\'\s*/>')

        # 优先尝试解析 XML 格式

        for match in xml_pattern.finditer(text):
            try:
                name = match.group(1)

                args = json.loads(match.group(2))

                invocations.append((name, args))

            except Exception as e:
                error_invocation = (
                    "__parse_error__",
                    {"original_line": match.group(0), "error": str(e)},
                )

                invocations.append(error_invocation)

        # 如果没有找到 XML 格式，尝试旧格式（向后兼容）

        if not invocations:
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
                    error_invocation = (
                        "__parse_error__",
                        {"original_line": line, "error": str(e)},
                    )

                    invocations.append(error_invocation)

        return invocations

    def _extract_response_and_error(self, text: str) -> Dict[str, str]:
        """提取 response 和 error 标记内容

        支持的标记：
        - <response>...</response>
        - <error>...</error>
        """
        result = {"response": "", "error": ""}

        # 提取 response 标记
        response_pattern = re.compile(r"<response>(.*?)</response>", re.DOTALL)
        response_match = response_pattern.search(text)
        if response_match:
            result["response"] = response_match.group(1).strip()

        # 提取 error 标记
        error_pattern = re.compile(r"<error>(.*?)</error>", re.DOTALL)
        error_match = error_pattern.search(text)
        if error_match:
            result["error"] = error_match.group(1).strip()

        return result

    def _get_system_prompt(self) -> str:
        """生成系统提示"""
        tool_list = self.tools.get_tool_list()

        tool_descriptions = "\n".join(
            f"工具名: {tool['function']['name']}\n"
            f"描述: {tool['function']['description']}\n"
            f"参数: {json.dumps(tool['function']['parameters'], ensure_ascii=False, indent=2)}\n"
            for tool in tool_list
        )

        return (
            "你是一个通用智能助手，帮助用户完成各种任务。\n\n"
            f"你有以下工具可以使用：\n\n{tool_descriptions}\n"
            "当你需要使用工具时，请使用以下格式输出：\n\n"
            "工具调用格式（XML 友好，支持流式传输）：\n"
            '<tool name="工具名" args=\'{"参数名": "参数值"}\'/>\n\n'
            "响应格式：\n"
            "<response>你的回复内容</response>\n\n"
            "错误格式：\n"
            "<error>错误描述</error>\n\n"
            "例如：\n"
            '<tool name="read_file" args=\'{"filename": "README.md"}\'/>\n'
            '<tool name="list_files" args=\'{"path": "."}\'/>\n'
            '<tool name="edit_file" args=\'{"path": "test.txt", "old_str": "hello", "new_str": "world"}\'/>\n'
            '<tool name="run_bash" args=\'{"command": "ls -la"}\'/>\n\n'
            "重要规则：\n"
            "1. 当用户询问关于当前项目、代码、文件等信息时，必须先使用工具（list_files、read_file）获取信息，不要凭空猜测\n"
            "2. 推荐使用 XML 格式，便于前端解析和流式传输\n"
            "3. JSON 参数必须使用单引号包裹，内部使用双引号\n"
            "4. 一次可以调用多个工具，每个工具一行\n"
            "5. 不需要工具时，使用 <response> 标记回复用户\n"
            "6. 遇到错误时，使用 <error> 标记描述问题\n"
            "7. 收到工具结果后，继续执行任务\n"
            "8. 直接执行任务，不要询问用户确认\n"
        )
