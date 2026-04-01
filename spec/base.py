# spec/base.py
from pydantic import BaseModel, Field
from typing import List, Dict

class TaskSpec(BaseModel):
    """生产级任务执行契约（Spec）"""
    task_type: str = Field(..., description="任务类型: chat / code / writing / analyze")
    overall_goal: str = Field(..., description="本次任务的核心目标")
    
    success_criteria: List[str] = Field(default_factory=list, description="可验证的成功标准（必须具体、可衡量）")
    progress_tracking: Dict = Field(default_factory=dict, description="进度记录：current_progress, completed_steps, remaining")
    
    process_requirements: List[str] = Field(default_factory=list, description="过程记录要求")
    boundaries: Dict[str, List[str]] = Field(
        default_factory=lambda: {
            "always": [],
            "ask_first": [],
            "never": []
        },
        description="Three-Tier Boundaries"
    )
    self_check_instructions: List[str] = Field(default_factory=list, description="自查机制")
    human_in_loop_points: List[str] = Field(default_factory=list, description="需要人类确认的点")
    
    additional_notes: str = Field("", description="其他备注")