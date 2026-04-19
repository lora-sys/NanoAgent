"""NanoAgent - 极简 Agent 框架"""

import json
import re
from typing import Any, Dict, List, Tuple, Callable, Optional

from core.spec import TaskSpec
from llm.client import NanoLLMClient
from tools.registry import ToolRegistry, get_tool_registry

try:
    from core.observability import get_tracer

    _HAS_OBSERVABILITY = True
except ImportError:
    _HAS_OBSERVABILITY = False


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

    def _should_use_chain(self, task: str) -> bool:
        """判断是否应该使用提示链模式"""
        # 明确提到"提示链"才使用链模式
        if "提示链" in task:
            return True

        # 工具调用意图检测（case-insensitive）
        task_lower = task.lower()
        tool_intent_keywords = {
            "读取",
            "打开",
            "list",
            "read",
            "read_file",
            "list_files",
            "README",
            "文件",
            "目录",
            "列出",
            "查看",
            "搜索",
            "执行",
            "运行",
            "命令",
        }

        # 如果任务包含工具意图关键词，不使用链模式
        if any(kw.lower() in task_lower for kw in tool_intent_keywords):
            return False

        # 复杂分析任务才使用链模式（明确排除工具导向任务）
        complex_keywords = {
            "分析",
            "设计",
            "评估",
            "规划",
            "优化",
            "总结",
            "架构",
            "项目",
            "框架",
            "最佳实践",
            "使用建议",
        }

        object_keywords = ("项目", "架构", "设计", "框架", "最佳实践")

        return any(kw in task for kw in complex_keywords) and any(
            obj in task for obj in object_keywords
        )

    def _run_with_chain(self, task: str) -> Dict[str, Any]:
        """使用提示链模式执行任务"""
        from core.chain import create_analysis_chain

        print("🔗 使用提示链模式执行任务")

        chain = create_analysis_chain()

        try:
            result = chain.run_sync(task, self.llm)
        except Exception as e:
            print(f"❌ 提示链执行失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "iterations": 0,
                "tools_used": [],
                "artifacts": [],
                "spec_file": None,
                "execution_mode": "chain",
                "execution_time": 0,
            }

        print("✅ 提示链执行完成")
        print(f"⏱️ 执行时间: {result.execution_time:.2f}秒")
        print(f"📋 执行步骤: {[h['step'] for h in result.context.history]}")
        print(f"\n🤖 {result.final_output}")

        return {
            "status": "completed" if result.success else "failed",
            "iterations": len(result.context.history),
            "tools_used": [h["step"] for h in result.context.history],
            "artifacts": [],
            "spec_file": None,
            "execution_mode": "chain",
            "execution_time": result.execution_time,
            "chain_result": result.to_dict(),
        }

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
        # 开始追踪会话
        if _HAS_OBSERVABILITY:
            tracer = get_tracer()
            tracer.start_session(task)

        try:
            # 智能选择执行模式
            if self._should_use_chain(task):
                return self._run_with_chain(task)

            # 传统 Agent 模式
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
                self._execute_tool_invocations(tool_invocations)

            # 保存任务规范
            spec_file = self.spec.save()
            print(f"\n💾 任务规范: {spec_file}")

            # 提取最后的 assistant 响应
            last_response = ""
            for msg in reversed(self.conversation):
                if msg.get("role") == "assistant":
                    last_response = msg.get("content", "")
                    break

            return {
                "status": self.spec.status,
                "iterations": iteration,
                "tools_used": self.spec.tools_used,
                "artifacts": self.spec.artifacts,
                "spec_file": spec_file,
                "execution_mode": "traditional",
                "conversation": self.conversation,
                "response": last_response,
            }
        finally:
            # 结束追踪会话
            if _HAS_OBSERVABILITY:
                tracer = get_tracer()
                tracer.end_session(self.spec.status if self.spec else "completed")

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
                self._execute_tool_invocations(tool_invocations)

    def _execute_tool_invocations(
        self, tool_invocations: List[Tuple[str, Dict[str, Any]]]
    ) -> None:
        """执行工具调用列表

        Args:
            tool_invocations: 工具调用列表，每个元素是 (工具名, 参数) 元组
        """
        for tool_name, args in tool_invocations:
            print(f"\n🔧 {tool_name}({args})")

            # 如果在任务模式下，记录工具调用
            if self.spec:
                self.spec.add_tool_call(tool_name)

            try:
                result = self.tools.execute(tool_name, args)
                print(f"👁️ {result}")

                # 记录产物（仅在任务模式下）
                if self.spec and isinstance(result, dict) and "file_path" in result:
                    self._record_artifact(result["file_path"])

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

                if self.spec:
                    self.spec.add_error(error_msg)

                self.conversation.append(
                    {
                        "role": "user",
                        "content": f"tool_result({json.dumps({'error': error_msg}, ensure_ascii=False)})",
                    }
                )

    def _record_artifact(self, file_path: str) -> None:
        """记录产物文件

        Args:
            file_path: 文件路径（可能是绝对路径或相对路径）
        """
        try:
            from pathlib import Path

            cwd = Path.cwd()
            abs_path = Path(file_path).resolve()

            # 尝试转换为相对路径
            if abs_path.is_relative_to(cwd):
                rel_path = abs_path.relative_to(cwd)
                self.spec.add_artifact(str(rel_path))
            else:
                self.spec.add_artifact(file_path)
        except Exception:
            # 转换失败，使用原始路径
            self.spec.add_artifact(file_path)

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
            "## 工具使用指南\n\n"
            "### 何时使用工具\n"
            "1. 用户明确要求读取文件、列出目录、运行命令时\n"
            "2. 需要获取项目信息、代码内容时\n"
            "3. 需要执行系统操作时\n\n"
            "### 工具调用格式\n"
            '<tool name="工具名" args=\'{"参数名": "参数值"}\'/>\n\n'
            "### 重要规则\n"
            "1. **必须使用工具**: 当用户询问文件、目录、代码等信息时，必须先使用工具获取\n"
            "2. **不要猜测**: 不要凭空猜测文件内容或目录结构\n"
            "3. **参数格式**: JSON 参数必须使用单引号包裹，内部使用双引号\n"
            "4. **路径处理**: 支持相对路径和绝对路径，相对路径相对于当前工作目录\n"
            "5. **错误处理**: 如果工具返回错误，使用 <error> 标记描述问题\n\n"
            "### 工具示例\n\n"
            "#### read_file - 读取文件内容\n"
            '<tool name="read_file" args=\'{"path": "README.md"}\'/>\n\n'
            "#### list_files - 列出目录文件\n"
            '<tool name="list_files" args=\'{"path": "."}\'/>\n\n'
            "#### edit_file - 编辑文件内容\n"
            '<tool name="edit_file" args=\'{"path": "test.txt", "old_str": "hello", "new_str": "world"}\'/>\n\n'
            "#### run_bash - 执行系统命令\n"
            '<tool name="run_bash" args=\'{"command": "ls -la"}\'/>\n\n'
            "### 响应格式\n"
            "- 正常响应: <response>你的回复内容</response>\n"
            "- 错误响应: <error>错误描述</error>\n\n"
            "### 执行流程\n"
            "1. 分析用户需求\n"
            "2. 确定需要使用的工具\n"
            "3. 调用工具获取信息\n"
            "4. 基于工具结果提供回复\n"
            "5. 如果需要，继续调用其他工具\n"
        )
