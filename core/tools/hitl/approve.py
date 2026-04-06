"""决策审批工具（决策增强）"""
from pydantic import BaseModel, Field
from loguru import logger
from cli_interface import get_cli

class PresentDecisionApprovalInput(BaseModel):
    """决策审批输入"""
    analysis: str = Field(..., description="Agent 分析结果（200字内）")
    action: str = Field(..., description="建议行动（100字内）")
    risk: str = Field(default="low", description="风险等级：low/medium/high")

def present_decision_for_approval(
    analysis: str,
    action: str,
    risk: str = "low"
) -> str:
    """
    向人类展示决策，等待审批（决策增强）
    
    AI 提供分析和建议，人类做最终决策
    用于安全敏感操作或需要人类判断的场景
    """
    try:
        cli = get_cli()
        result = cli.display_decision(analysis, action, risk)
        logger.info(f"Decision {result}: {action}")
        return result
    except Exception as e:
        logger.error(f"Error in decision approval: {e}")
        return "error"