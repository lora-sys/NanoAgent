"""
NanoAgent 统一数据模型定义

所有 Pydantic 模型都集中在这个文件中，确保类型一致性和避免重复。
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal, Any
from enum import Enum


# ========== 任务相关 ==========


class TaskType(str, Enum):
    """任务类型枚举"""

    CODE = "code"
    WRITING = "writing"
    ANALYZE = "analyze"
    CHAT = "chat"


class TaskSpec(BaseModel):
    """生产级任务执行契约（Spec）"""

    task_type: str = Field(..., description="任务类型: chat / code / writing / analyze")
    overall_goal: str = Field(..., description="本次任务的核心目标")

    success_criteria: List[str] = Field(
        default_factory=list, description="可验证的成功标准（必须具体、可衡量）"
    )
    progress_tracking: Dict = Field(
        default_factory=dict,
        description="进度记录：current_progress, completed_steps, remaining",
    )

    process_requirements: List[str] = Field(
        default_factory=list, description="过程记录要求"
    )
    boundaries: Dict[str, List[str]] = Field(
        default_factory=lambda: {"always": [], "ask_first": [], "never": []},
        description="Three-Tier Boundaries",
    )
    self_check_instructions: List[str] = Field(
        default_factory=list, description="自查机制"
    )
    human_in_loop_points: List[str] = Field(
        default_factory=list, description="需要人类确认的点"
    )

    additional_notes: str = Field("", description="其他备注")


# ========== 计划相关 ==========


class PlanStep(BaseModel):
    """计划步骤"""

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


# ========== Manifest 相关 ==========


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
        default_factory=lambda: {
            "master": ".spec/master_spec.md",
            "steps_dir": ".spec/steps/",
        }
    )
    pipeline: List[PipelineStage] = Field(default_factory=list)


# ========== 路由相关 ==========


class RoutingDecision(BaseModel):
    """路由决策结果"""

    task_type: TaskType
    confidence: float
    template_modules: List[str] = Field(default_factory=list)
    reasoning: str


# ========== 工具相关 ==========


class ToolCategory(str, Enum):
    """工具类别枚举"""

    FILE = "file"
    HITL = "hitl"
    CODE = "code"
    WEB = "web"


class ToolDefinition(BaseModel):
    """工具定义"""

    name: str
    description: str
    category: ToolCategory
    input_schema: Dict
    function: Any  # callable 类型在 Pydantic 中需要用 Any


# ========== 反思相关 ==========


class ReflectionResult(BaseModel):
    """反思结果"""

    task_completed: bool
    progress_summary: str
    issues_found: List[str] = Field(default_factory=list)
    solutions_applied: List[str] = Field(default_factory=list)
    next_action: str = "continue"
    confidence_score: float = 0.5


# ========== Spec 内容生成相关 ==========


class SpecContent(BaseModel):
    """Spec 内容模型（用于 LLM 生成）"""

    task_type: str
    overall_goal: str
    success_criteria: List[str] = Field(default_factory=list)
    current_progress: str = ""
    completed_steps: List[str] = Field(default_factory=list)
    remaining: List[str] = Field(default_factory=list)
    always: List[str] = Field(default_factory=list)
    ask_first: List[str] = Field(default_factory=list)
    never: List[str] = Field(default_factory=list)
    self_check_instructions: List[str] = Field(default_factory=list)
    process_requirements: List[str] = Field(default_factory=list)


class ArtifactSpec(BaseModel):
    """交付物规范模型"""

    name: str = Field(..., description="交付物名称")
    format: str = Field(
        ..., description="交付物格式（如：markdown, html, json, pdf等）"
    )
    acceptance_criteria: str = Field(..., description="验收标准")


class TemplateSpecContent(BaseModel):
    """模板 Spec 内容模型（用于模板填充）"""

    must_constraints: List[str] = Field(default_factory=list)
    must_not_constraints: List[str] = Field(default_factory=list)
    artifacts: List[ArtifactSpec] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)


# ========== 文件工具输入模型 ==========


class ReadFileInput(BaseModel):
    """读取文件输入"""

    filepath: str = Field(
        ...,
        description="文件路径(相对于 agent_workspace, 例如: 'main.py' 或 'src/app.py', 不要包含 'agent_workspace/' 前缀)",
    )


class WriteFileInput(BaseModel):
    """写入文件输入"""

    filepath: str = Field(
        ...,
        description="文件路径(相对于 agent_workspace, 例如: 'main.py' 或 'src/app.py', 不要包含 'agent_workspace/' 前缀)",
    )
    content: str = Field(..., description="要写入的内容")
    mode: str = Field(default="w", description="写入模式: w=覆盖, a=追加")


class ListDirectoryInput(BaseModel):
    """列出目录输入"""

    path: str = Field(default=".", description="目录路径（相对于 agent_workspace）")


# ========== HITL 工具输入模型 ==========


class AskUserQuestionInput(BaseModel):
    """向用户提问输入"""

    question: str = Field(..., description="要向用户提出的问题")
    options: Optional[list[str]] = Field(
        default=None, description="可选的答案选项(如果有)"
    )


class PresentDecisionApprovalInput(BaseModel):
    """决策审批输入"""

    analysis: str = Field(..., description="Agent 分析结果(200字内)")
    action: str = Field(..., description="建议行动(100字内)")
    risk: str = Field(default="low", description="风险等级: low/medium/high")


class MonitorAgentInput(BaseModel):
    """监控 Agent 输入"""

    observation: str = Field(..., description="观察内容")


class HumanInterventionInput(BaseModel):
    """人工干预输入"""

    instruction: str = Field(..., description="干预指令")


class CollectFeedbackInput(BaseModel):
    """收集反馈输入"""

    feedback_type: str = Field(
        ..., description="反馈类型: satisfaction/suggestion/bug_report"
    )
    prompt: str = Field(default="", description="提示信息")


class EscalateToHumanInput(BaseModel):
    """升级到人工输入"""

    reason: str = Field(..., description="升级原因")
    context: str = Field(..., description="上下文信息")


# ========== 验证结果 ==========


class ValidationResult(BaseModel):
    """验证结果"""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ========== 执行结果 ==========


class ExecutionResult(BaseModel):
    """执行结果"""

    status: Literal["completed", "failed", "interrupted"]
    steps_executed: int
    observations_count: int
    reflections_count: int
    final_reflection: Optional[Dict] = None
    message: str
    artifacts: List[str] = Field(default_factory=list)
