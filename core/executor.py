"""
执行器 - NanoAgent（简化版）

负责编排 ReAct 循环，各个阶段委托给独立的处理器
"""

from typing import Dict, Any, Optional, List
from loguru import logger
import json

from core.interfaces import (
    ILLMClient,
    IRouter,
    IManifestManager,
    IContextLoader,
    ISpecGenerator,
)
from core.phases import (
    ThinkingPhase,
    ActingPhase,
    ObservingPhase,
    ReflectionPhase,
    PlanningPhase,
)
from core.utils import get_timestamp, get_recent_observations_summary
from spec.models import AgentPlan


class AgentExecutor:
    """执行器 - 编排器模式"""

    def __init__(
        self,
        llm_client: ILLMClient,
        router: IRouter,
        manifest_manager: IManifestManager,
        context_loader: IContextLoader,
        spec_generator: ISpecGenerator,
        tool_registry: Optional[Any] = None,
        persistence_manager: Optional[Any] = None,
        cache: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None,
        state: Optional[Any] = None,
    ):
        """初始化执行器"""
        self.llm_client = llm_client
        self.router = router
        self.manifest_manager = manifest_manager
        self.context_loader = context_loader
        self.spec_generator = spec_generator
        self.tool_registry = tool_registry
        self.persistence_manager = persistence_manager
        self.cache = cache
        self.config = config or {}
        self.state = state

        # 初始化上下文管理器
        from .context_manager import ContextManager
        self.context_manager = ContextManager()

        # 初始化规则引擎
        from .rule_engine import RuleEngine
        self.rule_engine = RuleEngine()

        # 从配置读取参数
        core_config = self.config.get("core", {})
        performance_config = core_config.get("performance", {})
        self.max_steps = performance_config.get("max_steps", 20)
        self.max_context_tokens = performance_config.get("max_context_tokens", 3500)

        # 初始化阶段处理器
        self.thinking_phase = ThinkingPhase(
            llm_client=llm_client,
            tool_registry=tool_registry,
            config=config,
        )
        self.thinking_phase.max_steps = self.max_steps
        
        self.acting_phase = ActingPhase(
            llm_client=llm_client,
            tool_registry=tool_registry,
            config=config,
        )
        
        self.observing_phase = ObservingPhase(
            llm_client=llm_client,
            tool_registry=tool_registry,
            config=config,
        )
        
        self.reflection_phase_handler = ReflectionPhase(
            llm_client=llm_client,
            tool_registry=tool_registry,
            config=config,
        )
        
        self.planning_phase = PlanningPhase(
            llm_client=llm_client,
            tool_registry=tool_registry,
            config=config,
        )

    # ============ 代理方法 ============

    def route_task(self, task: str) -> Dict[str, Any]:
        """路由任务"""
        logger.info("=== Phase 1: Task Routing ===")
        return self.router.route(task)

    def should_init_spec(self, task: str, routing_decision: Dict[str, Any]) -> bool:
        """判断是否需要初始化 Spec"""
        from core.router import TaskType
        return routing_decision.get("task_type") == TaskType.CODE

    def load_context(self) -> Dict[str, Any]:
        """加载上下文"""
        logger.info("=== Phase 3: Dynamic Context Loading ===")
        context = self.context_loader.load_context()
        logger.info(f"Context loaded for stage: {context.get('current_stage_id', 'unknown')}")
        return context

    def update_context(self, updates: Dict[str, Any]) -> None:
        """更新上下文"""
        self.context_loader.update_context(updates)

    def planning_phase(self, task: str, context: Dict[str, Any]) -> AgentPlan:
        """Planning 阶段"""
        # 构建 spec 内容
        spec_content = ""
        if context.get("master_spec") and context.get("current_stage_spec"):
            spec_content = f"""【当前任务阶段】
{context.get('master_spec', '')[:300]}

## 当前阶段约束
{context.get('current_stage_spec', '')}
"""
        else:
            spec_content = "No spec context available"

        return self.planning_phase.execute(
            task=task,
            spec_content=spec_content,
            current_context="",
        )

    def think_phase(
        self,
        task: str,
        context: Dict[str, Any],
        observations: List[Dict[str, Any]],
        step_count: int = 0,
        spec: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Think 阶段"""
        return self.thinking_phase.execute(
            task=task,
            context=context,
            observations=observations,
            step_count=step_count,
            spec=spec,
            state=self.state,
        )

    def act_phase(self, action: Dict[str, Any]) -> Any:
        """Act 阶段"""
        return self.acting_phase.execute(action)

    def observe_phase(self, action: Dict[str, Any], result: Any) -> Dict[str, Any]:
        """Observe 阶段"""
        return self.observing_phase.execute(
            last_action=action,
            tool_result=result,
        )

    def reflection_phase(
        self, 
        observations: List[Dict[str, Any]], 
        spec: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Reflection 阶段"""
        return self.reflection_phase_handler.execute(
            execution_history=observations,
            task_spec=spec,
            current_progress={"observations_count": len(observations)},
            rule_engine=self.rule_engine,
        )

    # ============ 辅助方法 ============

    def build_system_prompt(self, context: Dict[str, Any]) -> str:
        """构建系统提示"""
        return f"""你是 NanoAgent 智能助手。

当前上下文：
- 阶段：{context.get('current_stage_id', 'unknown')}
- 任务：{context.get('task_goal', 'unknown')}

请按照 ReAct 循环执行任务：思考 → 行动 → 观察 → 反思"""

    def _truncate_context_for_tokens(self, context: str, max_tokens: Optional[int] = None) -> str:
        """截断上下文"""
        max_tokens = max_tokens or self.max_context_tokens
        # 粗略估计：1 token ≈ 4 字符
        max_chars = max_tokens * 4
        if len(context) > max_chars:
            return context[:max_chars] + "\n... [truncated]"
        return context

    def _build_context(self) -> Dict[str, Any]:
        """构建上下文"""
        return {
            "max_steps": self.max_steps,
            "max_context_tokens": self.max_context_tokens,
        }

    def _get_recent_observations_summary(
        self, observations: List[Dict[str, Any]], max_items: int = 3
    ) -> str:
        """获取最近观察摘要"""
        return get_recent_observations_summary(observations, max_items)

    def check_completion(self, observations: List[Dict[str, Any]], manifest: Any) -> bool:
        """检查是否完成"""
        if not observations:
            return False
        
        last_obs = observations[-1]
        return last_obs.get("action") == "complete"

    def init_spec(self, task: str) -> Any:
        """初始化 Spec"""
        logger.info("=== Initializing Spec ===")
        return self.spec_generator.generate(task)

    def load_existing_manifest(self) -> Any:
        """加载现有 Manifest"""
        try:
            return self.manifest_manager.load()
        except:
            return None

    def save_execution_result(self, decisions: List[str], artifacts: List[str]) -> None:
        """保存执行结果"""
        if self.manifest_manager:
            self.manifest_manager.save(decisions=decisions, artifacts=artifacts)

    def _get_timestamp(self) -> str:
        """获取时间戳"""
        return get_timestamp()

    def _extract_and_save_requirements(self, user_answer: str, action: Dict[str, Any]):
        """提取并保存需求"""
        if self.state:
            self.state.add_requirement(user_answer)

    def _extract_artifact_from_action(self, action: Dict[str, Any], result: Any) -> Optional[str]:
        """从动作中提取交付物"""
        if action.get("tool") in ["write_file", "safe_write_file"]:
            return action.get("arguments", {}).get("filepath", "unknown")
        return None

    def _extract_decision_from_answer(self, user_answer: str) -> Optional[str]:
        """从回答中提取决策"""
        if any(word in user_answer.lower() for word in ["确认", "好的", "没问题", "可以"]):
            return "confirmed"
        return None
