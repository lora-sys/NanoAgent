"""提示链模块 - 支持复杂任务拆解和链式执行"""

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional, Union

from core.context import ChainContext


class ChainResult:
    """链式执行结果"""

    def __init__(
        self,
        success: bool,
        final_output: Any,
        context: ChainContext,
        error: Optional[str] = None,
    ):
        self.success = success
        self.final_output = final_output
        self.context = context
        self.error = error
        self.execution_time: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "final_output": self.final_output,
            "context": self.context.to_dict(),
            "error": self.error,
            "execution_time": self.execution_time,
        }


class ChainStep:
    """单个链式步骤"""

    def __init__(
        self,
        name: str,
        prompt: str,
        handler: Optional[Callable[[ChainContext], Any]] = None,
    ):
        self.name = name
        self.prompt = prompt
        self.handler = handler

    async def execute(self, context: ChainContext, llm_client: Any) -> Any:
        """执行步骤"""
        # 如果有自定义处理器，使用处理器
        if self.handler:
            if asyncio.iscoroutinefunction(self.handler):
                return await self.handler(context)
            else:
                return self.handler(context)

        # 否则使用 LLM 处理
        if llm_client is None:
            raise ValueError("LLM client required for default execution")

        # 构建 LLM 输入
        llm_input = self._build_llm_input(context)

        # 调用 LLM - 优先使用异步方法，如果没有则使用同步方法
        if hasattr(llm_client, "achat") and asyncio.iscoroutinefunction(
            llm_client.achat
        ):
            result = await llm_client.achat([{"role": "user", "content": llm_input}])
        elif hasattr(llm_client, "chat"):
            result = llm_client.chat([{"role": "user", "content": llm_input}])
        else:
            raise ValueError("LLM client must have either 'achat' or 'chat' method")

        return result

    def _build_llm_input(self, context: ChainContext) -> str:
        """构建 LLM 输入"""
        # 格式化 prompt 使用上下文数据
        formatted_prompt = self.prompt
        try:
            formatted_prompt = self.prompt.format(**context.data)
        except (KeyError, ValueError) as e:
            # 如果格式化失败，使用原始 prompt
            import warnings

            warnings.warn(
                f"ChainStep '{self.name}' prompt format error: {e}. Using raw prompt."
            )

        parts = [formatted_prompt, ""]

        # 添加上下文信息
        if context.data:
            parts.append("上下文信息：")
            parts.extend(
                f"- {key}: {json.dumps(value, ensure_ascii=False)}"
                for key, value in context.data.items()
            )
            parts.append("")

        # 添加历史信息（最近3步）
        if context.history:
            parts.append("历史步骤：")
            parts.extend(
                f"- {item['step']}: {str(item['result'])[:100]}..."
                for item in context.history[-3:]
            )
            parts.append("")

        return "\n".join(parts)


class PromptChain:
    """提示链主类"""

    def __init__(
        self,
        steps: List[ChainStep],
        name: str = "default_chain",
        stop_on_error: bool = True,
        todo_list_id: Optional[str] = None,
    ):
        self.steps = steps
        self.name = name
        self.stop_on_error = stop_on_error
        self.todo_list_id = todo_list_id

    async def run(
        self,
        initial_input: Union[str, Dict[str, Any]],
        llm_client: Any,
        context: Optional[ChainContext] = None,
    ) -> ChainResult:
        """运行提示链"""
        import time

        start_time = time.time()

        # 初始化上下文
        if context is None:
            context = ChainContext()

        # 设置初始输入
        if isinstance(initial_input, str):
            context.set("input", initial_input)
        else:
            context.data.update(initial_input)

        # 执行每个步骤
        final_output = None
        error = None

        for step_idx, step in enumerate(self.steps):
            try:
                # 执行步骤
                result = await step.execute(context, llm_client)

                # 保存结果到上下文
                context.set(step.name, result)

                # 添加历史记录
                context.add_history(step.name, result)

                # 更新最终输出
                final_output = result

                # Auto-update todo if chain has todo_list_id
                if self.todo_list_id:
                    try:
                        from tools.todo import todo_update_status
                        todo_update_status(self.todo_list_id, step_idx, "done")
                    except Exception:
                        pass  # Don't fail chain execution on todo errors

            except Exception as e:
                error = f"步骤 '{step.name}' 执行失败: {str(e)}"
                context.add_history(step.name, {"error": error})

                if self.stop_on_error:
                    break

        # 创建结果
        result = ChainResult(
            success=error is None,
            final_output=final_output,
            context=context,
            error=error,
        )
        result.execution_time = time.time() - start_time

        return result

    def run_sync(
        self,
        initial_input: Union[str, Dict[str, Any]],
        llm_client: Any,
        context: Optional[ChainContext] = None,
    ) -> ChainResult:
        """同步运行提示链"""
        return asyncio.run(self.run(initial_input, llm_client, context))

    def add_step(self, step: ChainStep) -> None:
        """添加步骤"""
        self.steps.append(step)

    def remove_step(self, step_name: str) -> bool:
        """移除步骤"""
        try:
            idx = next(i for i, step in enumerate(self.steps) if step.name == step_name)
            self.steps.pop(idx)
            return True
        except StopIteration:
            return False

    def get_step(self, step_name: str) -> Optional[ChainStep]:
        """获取步骤"""
        return next((step for step in self.steps if step.name == step_name), None)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "steps": [
                {"name": step.name, "prompt": step.prompt} for step in self.steps
            ],
            "stop_on_error": self.stop_on_error,
        }


def create_analysis_chain() -> PromptChain:
    """创建分析任务的标准提示链"""
    return PromptChain(
        [
            ChainStep(
                "分析需求",
                "分析用户需求，提取关键信息、目标和约束条件。请以 JSON 格式返回："
                '{"requirement": "需求描述", "goals": ["目标1", "目标2"], "constraints": ["约束1", "约束2"]}',
            ),
            ChainStep(
                "制定计划",
                "根据分析结果制定详细的执行计划。请以 JSON 格式返回："
                '{"steps": [{"step": "步骤1", "description": "描述"}, ...], "estimated_time": "预估时间"}',
            ),
            ChainStep(
                "执行分析", "按照计划执行分析任务，使用工具获取必要信息，完成分析工作。"
            ),
            ChainStep("总结结果", "总结分析结果，提供清晰的结论和建议。"),
        ],
        name="analysis_chain",
    )


def create_design_chain() -> PromptChain:
    """创建设计任务的标准提示链"""
    return PromptChain(
        [
            ChainStep(
                "理解需求", "深入理解设计需求，明确目标用户、使用场景和核心功能。"
            ),
            ChainStep("设计方案", "基于需求设计方案，包括架构、接口和数据结构。"),
            ChainStep("验证设计", "验证设计的可行性和合理性，识别潜在问题。"),
            ChainStep("完善方案", "根据验证结果完善设计方案，提供最终建议。"),
        ],
        name="design_chain",
    )
