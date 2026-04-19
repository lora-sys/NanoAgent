"""增强提示链模块 - 支持门控机制和质量验证"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime

from core.context import ChainContext


@dataclass
class GateResult:
    """门控检查结果"""

    passed: bool
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "passed": self.passed,
            "message": self.message,
            "metadata": self.metadata,
        }


@dataclass
class QualityCheck:
    """质量检查结果"""

    score: float  # 0.0-1.0
    passed: bool
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "score": self.score,
            "passed": self.passed,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


class EnhancedChainContext(ChainContext):
    """增强链式执行上下文"""

    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        super().__init__(initial_data)
        self.gate_results: List[GateResult] = []
        self.quality_checks: List[QualityCheck] = []

    def add_history(
        self, step_name: str, result: Any, gate_result: Optional[GateResult] = None
    ) -> None:
        """添加执行历史"""
        self.history.append(
            {
                "step": step_name,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "gate_result": gate_result.to_dict() if gate_result else None,
            }
        )

    def add_gate_result(self, result: GateResult) -> None:
        """添加门控检查结果"""
        self.gate_results.append(result)

    def add_quality_check(self, check: QualityCheck) -> None:
        """添加质量检查结果"""
        self.quality_checks.append(check)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        base = super().to_dict()
        base.update(
            {
                "gate_results": [r.to_dict() for r in self.gate_results],
                "quality_checks": [c.to_dict() for c in self.quality_checks],
            }
        )
        return base


class EnhancedChainStep:
    """增强链式步骤"""

    def __init__(
        self,
        name: str,
        prompt: str,
        handler: Optional[Callable[[EnhancedChainContext], Any]] = None,
        gate_check: Optional[Callable[[str], GateResult]] = None,
        quality_check: Optional[Callable[[str], QualityCheck]] = None,
        retry_on_fail: bool = False,
        max_retries: int = 3,
    ):
        self.name = name
        self.prompt = prompt
        self.handler = handler
        self.gate_check = gate_check
        self.quality_check = quality_check
        self.retry_on_fail = retry_on_fail
        self.max_retries = max_retries

    async def execute(
        self,
        context: EnhancedChainContext,
        llm_client: Any,
    ) -> tuple[Any, GateResult, QualityCheck]:
        """执行步骤"""
        result = None
        gate_result = None
        quality_check = None

        # 尝试执行（支持重试）
        for attempt in range(self.max_retries):
            try:
                # 如果有自定义处理器，使用处理器
                if self.handler:
                    if asyncio.iscoroutinefunction(self.handler):
                        result = await self.handler(context)
                    else:
                        result = self.handler(context)
                else:
                    # 否则使用 LLM 处理
                    if llm_client is None:
                        raise ValueError("LLM client required for default execution")

                    llm_input = self._build_llm_input(context)

                    if hasattr(llm_client, "achat") and asyncio.iscoroutinefunction(
                        llm_client.achat
                    ):
                        result = await llm_client.achat(
                            [{"role": "user", "content": llm_input}]
                        )
                    elif hasattr(llm_client, "chat"):
                        result = llm_client.chat(
                            [{"role": "user", "content": llm_input}]
                        )
                    else:
                        raise ValueError(
                            "LLM client must have either 'achat' or 'chat' method"
                        )

                # 门控检查
                if self.gate_check:
                    gate_result = self.gate_check(str(result))
                    context.add_gate_result(gate_result)

                    if not gate_result.passed:
                        if self.retry_on_fail and attempt < self.max_retries - 1:
                            continue  # 重试
                        else:
                            break  # 放弃

                # 质量检查
                if self.quality_check:
                    quality_check = self.quality_check(str(result))
                    context.add_quality_check(quality_check)

                    if not quality_check.passed:
                        if self.retry_on_fail and attempt < self.max_retries - 1:
                            continue  # 重试
                        else:
                            break  # 放弃

                break  # 成功执行

            except Exception:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(0.1)  # 短暂延迟后重试

        return result, gate_result, quality_check

    def _build_llm_input(self, context: EnhancedChainContext) -> str:
        """构建 LLM 输入"""
        parts = [self.prompt, ""]

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


class EnhancedPromptChain:
    """增强提示链主类"""

    def __init__(
        self,
        steps: List[EnhancedChainStep],
        name: str = "enhanced_chain",
        stop_on_error: bool = True,
        stop_on_gate_fail: bool = True,
        stop_on_quality_fail: bool = False,
    ):
        self.steps = steps
        self.name = name
        self.stop_on_error = stop_on_error
        self.stop_on_gate_fail = stop_on_gate_fail
        self.stop_on_quality_fail = stop_on_quality_fail

    async def run(
        self,
        initial_input: Union[str, Dict[str, Any]],
        llm_client: Any,
        context: Optional[EnhancedChainContext] = None,
    ) -> Dict[str, Any]:
        """运行增强提示链"""
        import time

        start_time = time.time()

        # 初始化上下文
        if context is None:
            context = EnhancedChainContext()

        # 设置初始输入
        if isinstance(initial_input, str):
            context.set("input", initial_input)
        else:
            context.data.update(initial_input)

        # 执行每个步骤
        final_output = None
        error = None
        gate_failed = False
        quality_failed = False

        for step in self.steps:
            try:
                # 执行步骤
                result, gate_result, quality_check = await step.execute(
                    context, llm_client
                )

                # 检查门控
                if gate_result and not gate_result.passed:
                    gate_failed = True
                    if self.stop_on_gate_fail:
                        error = (
                            f"步骤 '{step.name}' 门控检查失败: {gate_result.message}"
                        )
                        break

                # 检查质量
                if quality_check and not quality_check.passed:
                    quality_failed = True
                    if self.stop_on_quality_fail:
                        error = (
                            f"步骤 '{step.name}' 质量检查失败: {quality_check.issues}"
                        )
                        break

                # 保存结果到上下文
                context.set(step.name, result)

                # 添加历史记录
                context.add_history(step.name, result, gate_result)

                # 更新最终输出
                final_output = result

            except Exception as e:
                error = f"步骤 '{step.name}' 执行失败: {str(e)}"
                context.add_history(step.name, {"error": error}, None)

                if self.stop_on_error:
                    break

        # 创建结果
        result = {
            "success": error is None,
            "final_output": final_output,
            "context": context.to_dict(),
            "error": error,
            "execution_time": time.time() - start_time,
            "gate_failed": gate_failed,
            "quality_failed": quality_failed,
            "steps_executed": len(context.history),
        }

        return result

    def run_sync(
        self,
        initial_input: Union[str, Dict[str, Any]],
        llm_client: Any,
        context: Optional[EnhancedChainContext] = None,
    ) -> Dict[str, Any]:
        """同步运行增强提示链"""
        return asyncio.run(self.run(initial_input, llm_client, context))


def create_document_creation_chain() -> EnhancedPromptChain:
    """创建文档创建链（示例）"""

    # 门控检查函数
    def check_outline_quality(outline: str) -> GateResult:
        """检查提纲质量"""
        if len(outline) < 50:
            return GateResult(
                passed=False,
                message="提纲太短，需要更详细的内容",
                metadata={"length": len(outline)},
            )
        return GateResult(
            passed=True,
            message="提纲质量良好",
            metadata={"length": len(outline)},
        )

    # 质量检查函数
    def check_content_quality(content: str) -> QualityCheck:
        """检查内容质量"""
        issues = []
        suggestions = []

        if len(content) < 100:
            issues.append("内容太短")
            suggestions.append("需要更详细的内容")

        if not any(char in content for char in "。！？"):
            issues.append("缺少句子结束标点")
            suggestions.append("添加适当的标点符号")

        score = 1.0 - (len(issues) * 0.2)
        score = max(0.0, min(1.0, score))

        return QualityCheck(
            score=score,
            passed=score >= 0.6,
            issues=issues,
            suggestions=suggestions,
        )

    return EnhancedPromptChain(
        [
            EnhancedChainStep(
                name="创建提纲",
                prompt="为以下主题创建详细的文档提纲",
                gate_check=check_outline_quality,
                retry_on_fail=True,
                max_retries=2,
            ),
            EnhancedChainStep(
                name="检查提纲",
                prompt="检查提纲是否符合文档要求，包括结构完整性、内容覆盖度等",
            ),
            EnhancedChainStep(
                name="撰写内容",
                prompt="基于提纲撰写完整的文档内容",
                quality_check=check_content_quality,
                retry_on_fail=True,
                max_retries=2,
            ),
            EnhancedChainStep(
                name="翻译内容",
                prompt="将文档内容翻译成另一种语言（如需要）",
            ),
        ],
        name="document_creation_chain",
        stop_on_gate_fail=True,
        stop_on_quality_fail=False,
    )


def create_marketing_chain() -> EnhancedPromptChain:
    """创建营销内容链（示例）"""

    # 质量检查函数
    def check_marketing_quality(content: str) -> QualityCheck:
        """检查营销内容质量"""
        issues = []
        suggestions = []

        if len(content) < 50:
            issues.append("内容太短")
            suggestions.append("需要更具吸引力的营销文案")

        if not any(char in content for char in "！？"):
            issues.append("缺少感叹号或问号")
            suggestions.append("添加更多情感化的标点符号")

        if "优惠" not in content and "折扣" not in content:
            suggestions.append("考虑添加优惠信息")

        score = 1.0 - (len(issues) * 0.15)
        score = max(0.0, min(1.0, score))

        return QualityCheck(
            score=score,
            passed=score >= 0.7,
            issues=issues,
            suggestions=suggestions,
        )

    return EnhancedPromptChain(
        [
            EnhancedChainStep(
                name="生成营销文案",
                prompt="为产品生成有吸引力的营销文案",
                quality_check=check_marketing_quality,
                retry_on_fail=True,
            ),
            EnhancedChainStep(
                name="翻译文案",
                prompt="将营销文案翻译成目标语言",
            ),
        ],
        name="marketing_chain",
        stop_on_quality_fail=False,
    )
