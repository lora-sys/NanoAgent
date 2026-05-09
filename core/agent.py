"""NanoAgent - 极简 Agent 框架"""

import json
import re
from typing import Any, Dict, List, Tuple, Callable, Optional

from core.utils import normalize_tool_calls

from core.lifecycle import (
    Lifecycle,
    AgentStartEvent,
    AgentEndEvent,
    TurnStartEvent,
    TurnEndEvent,
    TurnContext,
    MessageStartEvent,
    MessageUpdateEvent,
    MessageEndEvent,
    ToolStartEvent,
    ToolUpdateEvent,
    ToolEndEvent,
)
from core.spec import TaskSpec
from core.tool_cache import get_tool_cache
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
        memory_integrator=None,
        executor=None,
    ):
        """
        初始化 Agent

        Args:
            llm_client: LLM 客户端，默认自动创建
            tool_registry: 工具注册表，默认自动创建
            memory_integrator: 可选，内存集成器（来自 core.memory）
            executor: 可选，并行执行器（来自 core.executor）
        """
        self.llm = llm_client or NanoLLMClient()
        self.tools = tool_registry or get_tool_registry()
        self.lifecycle = Lifecycle()
        if _HAS_OBSERVABILITY:
            self.lifecycle.subscribe(get_tracer())
        self.spec: Optional[TaskSpec] = None
        self.conversation: List[Dict[str, str]] = []
        self._stop_condition: Optional[Callable[[], bool]] = None
        self._memory_integrator = memory_integrator
        self._executor = executor

    def _should_use_executor(self, task: str) -> bool:
        """判断是否应该使用并行执行器模式"""
        if not self._executor:
            return False

        # 检测并行任务关键词
        parallel_keywords = {
            "并行",
            "parallel",
            "同时",
            "一起",
            "全部",
            "多个",
            "分别",
        }

        # 多目标分隔符
        separators = ["和", "与", "以及", ",", "，", "、"]

        # 有明确的并行指示词
        if any(kw in task for kw in parallel_keywords):
            return True

        # 检测多目标模式 (逗号、或列表分隔)
        for sep in separators:
            if sep in task and task.count(sep) >= 1:
                return True

        return False

    def _run_with_executor(self, task: str) -> Dict[str, Any]:
        """使用并行执行器模式执行任务"""
        from core.executor import ExecutionGraph, TaskNode, SerialExecutor
        import time

        print("⚡ 使用并行执行器模式执行任务")

        try:
            # 构建执行图 - 将任务分解为多个步骤
            steps = self._decompose_task(task)
            if not steps:
                return self._run_with_chain(task)

            # 创建执行图
            graph = ExecutionGraph(name="agent_executor")

            for i, step in enumerate(steps):
                node = TaskNode(
                    id=f"step_{i}",
                    name=step.get("name", f"Step {i}"),
                    prompt=step.get("prompt", task),
                    handler=None,  # Will use LLM
                )
                if i > 0:
                    node.depends_on = [f"step_{i - 1}"]
                graph.add_node(node)

            graph.entry_point = "step_0"

            # 使用串行执行器（与 agent 循环相同）
            executor = SerialExecutor(llm_client=self.llm)

            start_time = time.time()
            status = executor.run_sync(graph, initial_input=task)
            duration = time.time() - start_time

            print("✅ 执行器模式执行完成")
            print(f"⏱️ 执行时间: {duration:.2f}秒")
            print(f"📋 执行步骤: {list(status.results.keys())}")

            return {
                "status": "completed"
                if all(r.status.value == "completed" for r in status.results.values())
                else "failed",
                "iterations": len(steps),
                "tools_used": [],
                "artifacts": [],
                "spec_file": None,
                "execution_mode": "executor",
                "execution_time": duration,
                "response": list(status.results.values())[-1].output
                if status.results
                else None,
                "executor_results": {k: v.to_dict() for k, v in status.results.items()},
            }

        except Exception as e:
            print(f"❌ 执行器模式执行失败: {e}")
            # Fallback to chain mode
            return self._run_with_chain(task)

    def _decompose_task(self, task: str) -> List[Dict[str, str]]:
        """将任务分解为多个步骤"""
        # 简单的基于关键词的分解
        # 实际应用中可使用 LLM 来分解
        separators = ["和", "与", "以及", ",", "，", "、"]

        parts = [task]
        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            if len(new_parts) > len(parts):
                parts = new_parts
                break

        if len(parts) > 1:
            return [
                {"name": f"subtask_{i}", "prompt": p.strip()}
                for i, p in enumerate(parts)
                if p.strip()
            ]

        return []

    def _should_use_chain(self, task: str) -> bool:
        """判断是否应该使用提示链模式"""
        # 明确提到"提示链"才使用链模式
        if "提示链" in task:
            return True

        # 工具调用意图检测(case-insensitive)
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

        # 复杂分析任务才使用链模式(明确排除工具导向任务)
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
            "tools_used": [],  # chain steps are internal, not real tool calls
            "artifacts": [],
            "spec_file": None,
            "execution_mode": "chain",
            "execution_time": result.execution_time,
            "response": result.final_output,
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
            max_iterations: 最大迭代次数(可选，默认无限制)
            stop_condition: 停止条件函数(可选)

        Returns:
            任务执行结果
        """
        # AgentStartEvent 会通过 lifecycle handler 触发 Tracer.start_session
        self.lifecycle.emit(AgentStartEvent(task=task))

        try:
            # 智能选择执行模式
            if self._should_use_executor(task):
                return self._run_with_executor(task)

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

            # Memory context injection
            if self._memory_integrator:
                self._memory_integrator.on_agent_start(task)
                # If integrator modified conversation[0] (system), we're good
                # Otherwise inject memory via dedicated call
                if self._memory_integrator.mm:
                    # Pass task for adaptive token budgets
                    mem_ctx = self._memory_integrator.mm.build_context_for_prompt(
                        max_tokens=1500, task=task
                    )
                    if mem_ctx:
                        self.conversation[0]["content"] += (
                            f"\n\n## Memory Context\n{mem_ctx}\n"
                        )

            print("🤖 NanoAgent - 极简 Agent 框架")
            print(f"📋 任务: {task}")

            # 主循环 - 无限制，直到条件满足
            iteration = 0
            while True:
                iteration += 1

                self.lifecycle.emit(
                    TurnStartEvent(
                        turn_context=TurnContext(
                            turn_number=self.lifecycle.get_turn_number() + 1,
                            iteration=iteration,
                        )
                    )
                )

                # 检查停止条件
                if max_iterations and iteration > max_iterations:
                    self.spec.fail(f"达到最大迭代次数 ({max_iterations})")
                    self.lifecycle.emit(
                        TurnEndEvent(
                            turn_context=TurnContext(
                                turn_number=self.lifecycle.get_turn_number(),
                                iteration=iteration,
                            )
                        )
                    )
                    break

                if self._stop_condition and self._stop_condition():
                    self.spec.complete()
                    self.lifecycle.emit(
                        TurnEndEvent(
                            turn_context=TurnContext(
                                turn_number=self.lifecycle.get_turn_number(),
                                iteration=iteration,
                            )
                        )
                    )
                    break

                # 调用 LLM with structured function calling
                self.lifecycle.emit(
                    MessageStartEvent(turn_number=self.lifecycle.get_turn_number())
                )
                tools = self.tools.get_tool_list()
                try:
                    assistant_content, tool_calls = self.llm.chat_with_tools(
                        self.conversation, tools
                    )
                except Exception as e:
                    self.spec.add_error(f"LLM 错误: {e}")
                    self.spec.fail(f"LLM 调用失败: {e}")
                    self.lifecycle.emit(
                        MessageEndEvent(
                            turn_number=self.lifecycle.get_turn_number(),
                            content="",
                            tool_calls=[],
                        )
                    )
                    self.lifecycle.emit(
                        TurnEndEvent(
                            turn_context=TurnContext(
                                turn_number=self.lifecycle.get_turn_number(),
                                iteration=iteration,
                            )
                        )
                    )
                    break

                self.lifecycle.emit(
                    MessageUpdateEvent(
                        turn_number=self.lifecycle.get_turn_number(),
                        delta=assistant_content,
                    )
                )

                self.conversation.append(
                    {"role": "assistant", "content": assistant_content}
                )
                normalized_tool_calls = normalize_tool_calls(tool_calls)

                self.lifecycle.emit(
                    MessageEndEvent(
                        turn_number=self.lifecycle.get_turn_number(),
                        content=assistant_content,
                        tool_calls=normalized_tool_calls,
                    )
                )

                if not normalized_tool_calls:
                    # 没有工具调用，任务完成
                    print(f"\n🤖 {assistant_content}")
                    self.spec.complete()
                    self.lifecycle.emit(
                        TurnEndEvent(
                            turn_context=TurnContext(
                                turn_number=self.lifecycle.get_turn_number(),
                                iteration=iteration,
                            )
                        )
                    )
                    break

                # 执行工具调用
                self._execute_tool_invocations(normalized_tool_calls)

                self.lifecycle.emit(
                    TurnEndEvent(
                        turn_context=TurnContext(
                            turn_number=self.lifecycle.get_turn_number(),
                            iteration=iteration,
                        )
                    )
                )

            # 保存任务规范
            spec_file = self.spec.save()
            print(f"\n💾 任务规范: {spec_file}")

            # 提取最后的 assistant 响应
            last_response = ""
            for msg in reversed(self.conversation):
                if msg.get("role") == "assistant":
                    last_response = msg.get("content", "")
                    break

            # Save session summary to cross-session memory
            if self._memory_integrator:
                self._memory_integrator.on_agent_end(task, last_response)

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
            total_turns, total_tools = self.lifecycle.get_totals()
            self.lifecycle.emit(
                AgentEndEvent(
                    status=self.spec.status if self.spec else "completed",
                    total_turns=total_turns,
                    total_tools=total_tools,
                )
            )
            # AgentEndEvent 会通过 lifecycle handler 触发 Tracer.end_session

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

                # 调用 LLM with structured function calling
                try:
                    tools = self.tools.get_tool_list()
                    assistant_content, tool_calls = self.llm.chat_with_tools(
                        self.conversation, tools
                    )
                except Exception as e:
                    print(f"\n❌ LLM 错误: {e}")
                    break

                normalized_tool_calls = normalize_tool_calls(tool_calls)

                if not normalized_tool_calls:
                    print(f"\n🤖 助手: {assistant_content}")
                    self.conversation.append(
                        {"role": "assistant", "content": assistant_content}
                    )
                    break

                # 执行工具调用
                self._execute_tool_invocations(normalized_tool_calls)

    def _execute_tool_invocations(self, tool_invocations: List[Dict[str, Any]]) -> None:
        """Execute tool calls from normalized {"name", "arguments"} dicts."""
        for tool_call in tool_invocations:
            name = tool_call.get("name", "")
            raw_args = tool_call.get("arguments", "{}")
            if isinstance(raw_args, str):
                try:
                    args = json.loads(raw_args)
                except Exception:
                    args = {}
            else:
                args = raw_args
            print(f"\n🔧 {name}({args})")

            # 如果在任务模式下，记录工具调用
            if self.spec:
                self.spec.add_tool_call(name)

            self.lifecycle.emit(
                ToolStartEvent(
                    turn_number=self.lifecycle.get_turn_number(),
                    tool_call_id=f"tc_{self.lifecycle._total_tools}",
                    tool_name=name,
                    args=args,
                )
            )

            try:
                result = self.tools.execute(name, args)
                print(f"👁️ {result}")

                self.lifecycle.emit(
                    ToolUpdateEvent(
                        turn_number=self.lifecycle.get_turn_number(),
                        tool_call_id=f"tc_{self.lifecycle._total_tools}",
                        tool_name=name,
                        partial_result=result,
                    )
                )

                # 记录产物(仅在任务模式下)
                if self.spec and isinstance(result, dict) and "file_path" in result:
                    self._record_artifact(result["file_path"])

                # 摘要后加入 context(减少 token 消耗)
                cache = get_tool_cache()
                summarized = cache.summarize(name, result)
                self.conversation.append(
                    {
                        "role": "user",
                        "content": f"tool_result({json.dumps(summarized, ensure_ascii=False)})",
                    }
                )

                # Track tool usage in memory integrator
                if self._memory_integrator:
                    self._memory_integrator.on_tool_call(name)
                    self._memory_integrator.on_turn_end(name, result)

                self.lifecycle.emit(
                    ToolEndEvent(
                        turn_number=self.lifecycle.get_turn_number(),
                        tool_call_id=f"tc_{self.lifecycle._total_tools}",
                        tool_name=name,
                        result=result,
                        is_error=False,
                    )
                )
            except Exception as e:
                error_msg = f"工具执行失败: {e}"
                print(f"❌ {error_msg}")

                if self.spec:
                    self.spec.add_error(error_msg)

                self.conversation.append(
                    {
                        "role": "user",
                        "content": f"tool_result({json.dumps({'tool': name, 'status': 'error', 'error': error_msg}, ensure_ascii=False)})",
                    }
                )

                self.lifecycle.emit(
                    ToolEndEvent(
                        turn_number=self.lifecycle.get_turn_number(),
                        tool_call_id=f"tc_{self.lifecycle._total_tools}",
                        tool_name=name,
                        result=str(e),
                        is_error=True,
                    )
                )

    def _record_artifact(self, file_path: str) -> None:
        """记录产物文件

        Args:
            file_path: 文件路径(可能是绝对路径或相对路径)
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

        1. 新格式(推荐)：<tool name="xxx" args='{"key":"value"}'/>

        2. 旧格式(兼容)：tool: name({"key":"value"})

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

        # 如果没有找到 XML 格式，尝试旧格式(向后兼容)

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
            "3. 需要搜索文件内容、代码模式时(使用 grep)\n"
            "4. 需要执行系统操作时\n\n"
            "### 工具调用格式\n"
            '<tool name="工具名" args=\'{"参数名": "参数值"}\'/>\n\n'
            "### 重要规则\n"
            "1. **必须使用工具**: 当用户询问文件、目录、代码等信息时，必须先使用工具获取\n"
            "2. **不要猜测**: 不要凭空猜测文件内容或目录结构\n"
            "3. **参数格式**: JSON 参数必须使用单引号包裹，内部使用双引号\n"
            "4. **路径处理**: 支持相对路径和绝对路径，相对路径相对于当前工作目录\n"
            "5. **错误处理**: 如果工具返回错误，使用 <error> 标记描述问题\n\n"
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
