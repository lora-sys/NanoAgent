"""数据模型"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class ThinkAction(BaseModel):
    action: str = Field(..., description="操作类型: tool_call, complete, wait, stage_complete")
    tool: Optional[str] = Field(None, description="工具名称")
    arguments: Optional[Dict[str, object]] = Field(None, description="工具参数")
    reason: Optional[str] = Field(None, description="决策原因")
    next_stage: Optional[str] = Field(None, description="下一阶段")


class Spec(BaseModel):
    task: str = Field(default="", description="任务描述")
    status: str = Field(default="running", description="状态")
    artifacts: List[Dict[str, str]] = Field(default_factory=list)
    decisions: List[Dict[str, str]] = Field(default_factory=list)
    current_stage: str = Field(default="unknown", description="当前阶段")
