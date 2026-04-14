"""
NanoAgent 统一数据模型定义
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from enum import Enum


class TaskType(str, Enum):
    """任务类型"""
    CODE = "code"
    WRITING = "writing"
    ANALYZE = "analyze"
    CHAT = "chat"


class TaskSpec(BaseModel):
    """任务执行契约"""
    task_type: str = Field(..., description="任务类型")
    overall_goal: str = Field(..., description="核心目标")
    success_criteria: List[str] = Field(default_factory=list)
    progress_tracking: Dict = Field(default_factory=dict)
    process_requirements: List[str] = Field(default_factory=list)
    boundaries: Dict[str, List[str]] = Field(
        default_factory=lambda: {"always": [], "ask_first": [], "never": []}
    )
    self_check_instructions: List[str] = Field(default_factory=list)
    human_in_loop_points: List[str] = Field(default_factory=list)
    additional_notes: str = ""


class PlanStep(BaseModel):
    """执行计划中的步骤"""
    step_id: int
    goal: str
    suggested_tools: List[str] = Field(default_factory=list)
    depends_on: List[int] = Field(default_factory=list)
    success_criteria: str = ""
    risk_assessment: str = ""


class AgentPlan(BaseModel):
    """执行计划"""
    steps: List[PlanStep] = Field(default_factory=list)
    overall_goal: str = ""
    estimated_steps: int = 0
    critical_path: List[int] = Field(default_factory=list)


class PipelineStage(BaseModel):
    """Pipeline 阶段"""
    id: str
    name: str
    file: str
    status: Literal["pending", "active", "completed"] = "pending"


class Manifest(BaseModel):
    """Manifest 配置"""
    project_name: str
    status: Literal["initializing", "active", "completed"] = "initializing"
    current_stage: str = ""
    storage: Dict = Field(
        default_factory=lambda: {"master": ".spec/master_spec.md", "steps_dir": ".spec/steps/"}
    )
    pipeline: List[PipelineStage] = Field(default_factory=list)


class RoutingDecision(BaseModel):
    """路由决策"""
    task_type: TaskType
    confidence: float
    template_modules: List[str] = Field(default_factory=list)
    reasoning: str


class ReflectionResult(BaseModel):
    """反思结果"""
    task_completed: bool
    stage_completed: bool
    progress_summary: str
    issues_found: List[str] = Field(default_factory=list)
    solutions_applied: List[str] = Field(default_factory=list)
    next_action: str
    confidence_score: float = 0.5
    decisions: List[str] = Field(default_factory=list)
    artifacts: List[str] = Field(default_factory=list)


class ArtifactSpec(BaseModel):
    """交付物规范"""
    name: str = Field(..., description="交付物名称")
    format: str = Field(..., description="格式")
    acceptance_criteria: str = Field(..., description="验收标准")


class TemplateSpecContent(BaseModel):
    """模板 Spec 内容"""
    must_constraints: List[str] = Field(default_factory=list)
    must_not_constraints: List[str] = Field(default_factory=list)
    artifacts: List[ArtifactSpec] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
