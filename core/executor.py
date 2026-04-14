"""
执行器 - NanoAgent（简化版）

负责编排 ReAct 循环，各个阶段委托给独立的处理器
"""

from typing import Dict, Any, Optional, List
from loguru import logger

from core.phases import ThinkingPhase, ActingPhase, ReflectionPhase, PlanningPhase
from core.output_validator import validate_output
from domain.models.models import AgentPlan, RoutingDecision, TaskType


class AgentExecutor:
    """执行器 - 编排器模式"""

    def __init__(
        self,
        llm_client: Any,
        router: Any,
        manifest_manager: Any,
        context_loader: Any,
        tool_registry: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
        state: Optional[Any] = None,
    ):
        self.llm_client = llm_client
        self.router = router
        self.manifest_manager = manifest_manager
        self.context_loader = context_loader
        self.tool_registry = tool_registry
        self.config = config or {}
        self.state = state

        from infrastructure.persistence.context import ContextManager
        self.context_manager = ContextManager()

        # 从配置读取参数
        perf = self.config.get("core", {}).get("performance", {})
        self.max_steps = perf.get("max_steps", 20)
        self.max_context_tokens = perf.get("max_context_tokens", 3500)

        # 初始化阶段处理器
        self.thinking_phase = ThinkingPhase(
            llm_client=llm_client, tool_registry=tool_registry, config=config,
        )
        self.thinking_phase.max_steps = self.max_steps
        self.acting_phase = ActingPhase(
            llm_client=llm_client, tool_registry=tool_registry, config=config,
        )
        self.reflection_phase_handler = ReflectionPhase(
            llm_client=llm_client, tool_registry=tool_registry, config=config,
        )
        self.planning_phase_handler = PlanningPhase(
            llm_client=llm_client, tool_registry=tool_registry, config=config,
        )

    # ============ 核心编排方法 ============

    def route_task(self, task: str) -> RoutingDecision:
        """路由任务"""
        logger.info("=== Phase 1: Task Routing ===")
        return self.router.route(task)

    def should_init_spec(self, task: str, routing_decision: RoutingDecision) -> bool:
        """判断是否需要初始化 Spec"""
        return routing_decision.task_type == TaskType.CODE

    def load_context(self) -> Dict[str, Any]:
        """加载上下文，合并静态 Spec 约束和已积累的执行上下文"""
        logger.info("=== Loading Context ===")

        spec_context = self.context_loader.dynamic_load_context()
        stage_id = spec_context.get("current_stage_id", "unknown")
        saved_context = self.context_manager.load_context(stage_id) or {}

        merged = {
            **spec_context,
            "accumulated_decisions": saved_context.get("accumulated_decisions", []),
            "accumulated_artifacts": saved_context.get("accumulated_artifacts", []),
            "recent_observations": saved_context.get("recent_observations", []),
        }
        logger.info(f"Context loaded: {stage_id}")
        return merged

    def save_context(self, context_updates: Dict[str, Any]) -> None:
        """保存执行上下文"""
        stage_id = context_updates.get("current_stage_id")
        if not stage_id:
            spec_context = self.context_loader.dynamic_load_context()
            stage_id = spec_context.get("current_stage_id", "main")
        self.context_manager.update_context(stage_id, context_updates)

    def planning_phase(self, task: str, context: Dict[str, Any]) -> AgentPlan:
        """Planning 阶段"""
        spec_content = ""
        if context.get("master_spec") and context.get("current_stage_spec"):
            spec_content = (
                f"【当前任务阶段】\n"
                f"{context.get('master_spec', '')[:300]}\n\n"
                f"## 当前阶段约束\n"
                f"{context.get('current_stage_spec', '')}"
            )
        else:
            spec_content = "No spec context available"

        return self.planning_phase_handler.execute(
            task=task, spec_content=spec_content, current_context="",
        )

    def think_phase(
        self, task, context, observations, step_count=0, spec=None,
    ) -> Dict[str, Any]:
        """Think 阶段"""
        return self.thinking_phase.execute(
            task=task, context=context, observations=observations,
            step_count=step_count, spec=spec, state=self.state,
        )

    def act_phase(self, action: Dict[str, Any]) -> Any:
        """Act 阶段"""
        return self.acting_phase.execute(action)

    def reflection_phase(self, observations, spec=None) -> Dict[str, Any]:
        """Reflection 阶段"""
        return self.reflection_phase_handler.execute(
            execution_history=observations,
            task_spec=spec,
            current_progress={"observations_count": len(observations)},
        )

    # ============ 辅助方法 ============

    def build_system_prompt(self, context: Dict[str, Any]) -> str:
        """构建系统提示"""
        return (
            f"你是 NanoAgent 智能助手。\n\n"
            f"- 阶段：{context.get('current_stage_id', 'unknown')}\n"
            f"- 任务：{context.get('task_goal', 'unknown')}\n\n"
            f"请按照 ReAct 循环执行任务：思考 → 行动 → 观察 → 反思"
        )

    def init_spec(self, task, routing_decision, spec_initializer):
        """初始化 Spec"""
        logger.info("=== Initializing Spec ===")
        return spec_initializer.init_spec(task, routing_decision)

    def load_existing_manifest(self):
        """加载现有 Manifest"""
        try:
            return self.manifest_manager.load_manifest()
        except (AttributeError, FileNotFoundError, OSError) as e:
            logger.debug(f"No existing manifest found: {e}")
            return None

    def save_execution_result(self, decisions, artifacts):
        """保存执行结果"""
        if self.manifest_manager:
            self.manifest_manager.save(decisions=decisions, artifacts=artifacts)
