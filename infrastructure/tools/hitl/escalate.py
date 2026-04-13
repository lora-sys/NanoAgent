"""升级策略工具"""

from pydantic import BaseModel, Field
from loguru import logger
from typing import Optional
from enum import Enum
from cli_interface import get_cli


class EscalationLevel(str, Enum):
    """升级级别"""

    INFO = "info"  # 仅通知
    WARNING = "warning"  # 需要注意
    CRITICAL = "critical"  # 立即需要人类介入


class EscalateInput(BaseModel):
    """升级输入"""

    reason: str = Field(..., description="升级原因")
    level: EscalationLevel = Field(..., description="升级级别：info/warning/critical")
    context: str = Field(..., description="当前上下文")
    attempted_solutions: Optional[list[str]] = Field(
        default=None, description="已尝试的解决方案"
    )


def escalate_to_human(
    reason: str,
    level: str,
    context: str,
    attempted_solutions: Optional[list[str]] = None,
) -> str:
    """
    升级策略：超出能力范围时将任务升级给人类操作员

    按既定协议升级，防止错误发生
    适用场景：
    - Agent 无法处理的复杂任务
    - 需要人类专业知识
    - 关键决策需要人类判断
    - 多次尝试失败后的兜底
    """
    try:
        cli = get_cli()
        solution = cli.display_escalation(reason, level, context)
        logger.info(f"Task escalated (level={level}): {reason[:50]}...")
        return solution

    except ValueError:
        logger.error(f"Invalid escalation level: {level}")
        return f"Error: Invalid level '{level}'. Use info/warning/critical"
    except Exception as e:
        logger.error(f"Error in escalation: {e}")
        return f"Error: {str(e)}"
