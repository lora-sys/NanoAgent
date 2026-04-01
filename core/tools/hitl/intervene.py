"""干预与纠正工具"""
from pydantic import BaseModel, Field
from loguru import logger
from typing import Optional
import sys
sys.path.insert(0, "/home/lora/repos/nanoagent")
from cli_interface import get_cli

class InterveneInput(BaseModel):
    """干预输入"""
    reason: str = Field(..., description="请求干预的原因")
    current_state: str = Field(..., description="当前状态描述")
    options: Optional[list[str]] = Field(default=None, description="可能的解决方案选项")

def human_intervention(
    reason: str,
    current_state: str,
    options: Optional[list[str]] = None
) -> str:
    """
    人类干预与纠正
    
    当 Agent 遇到错误或模糊场景时请求人类介入
    操作员可以：
    - 纠正错误
    - 补充数据
    - 引导 Agent
    - 提供明确方向
    
    这有助于 Agent 后续改进
    """
    try:
        cli = get_cli()
        correction = cli.display_intervention(reason, current_state, options)
        logger.info(f"Human intervention provided: {correction[:100]}...")
        return correction
        
    except Exception as e:
        logger.error(f"Error in human intervention: {e}")
        return f"Error: {str(e)}"