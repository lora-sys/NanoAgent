"""
执行器 - NanoAgent
管理执行流程的各个阶段
"""
from typing import Dict, Any, Optional
from loguru import logger
from spec.models import AgentPlan, TaskSpec
from core.interfaces import ILLMClient, IRouter, IManifestManager, IContextLoader, ISpecGenerator


class AgentExecutor:
    """执行器 - 管理执行流程"""

    def __init__(
        self,
        llm_client: ILLMClient,
        router: IRouter,
        manifest_manager: IManifestManager,
        context_loader: IContextLoader,
        spec_generator: ISpecGenerator,
        cache: Any = None,
        max_steps: int = 20
    ):
        """
        初始化执行器

        Args:
            llm_client: LLM 客户端
            router: 路由器
            manifest_manager: Manifest 管理器
            context_loader: 上下文加载器
            spec_generator: Spec 生成器
            max_steps: 最大执行步数
        """
        self.llm_client = llm_client
        self.router = router
        self.manifest_manager = manifest_manager
        self.context_loader = context_loader
        self.spec_generator = spec_generator
        self.cache = cache
        self.max_steps = max_steps

    def route_task(self, task: str) -> Dict:
        """
        阶段1：智能路由

        Args:
            task: 用户任务

        Returns:
            路由决策结果
        """
        logger.info("=== Phase 1: Task Routing ===")
        routing_decision = self.router.route(task)
        logger.info(
            "Task routed",
            task_type=routing_decision.task_type.value,
            confidence=f"{routing_decision.confidence:.2%}"
        )
        return routing_decision.model_dump()

    def should_init_spec(self, task: str, routing_decision: Dict) -> bool:
        """
        判断是否需要初始化 Spec

        Args:
            task: 用户任务
            routing_decision: 路由决策

        Returns:
            是否需要初始化
        """
        # 简化逻辑：总是需要初始化
        return True

    def load_context(self) -> Dict:
        """
        阶段3：动态加载上下文

        Returns:
            上下文字典
        """
        logger.info("=== Phase 3: Dynamic Context Loading ===")
        context = self.context_loader.dynamic_load_context()
        logger.info("Context loaded", has_master=bool(context.get("master_spec")))
        return context

    def build_system_prompt(self, context: Dict) -> str:
        """
        构建系统提示（基于当前阶段的约束）

        Args:
            context: 上下文字典

        Returns:
            系统提示
        """
        if context.get("master_spec") and context.get("current_stage_spec"):
            return f"""【当前任务阶段】

## 核心目标（来自 Master Spec）
{context['master_spec'][:300]}

## 当前阶段约束
{context['current_stage_spec']}

## 必须遵守的规则
{chr(10).join(f'- {c}' for c in context.get('constraints', {}).get('always', []))}

## 禁止的操作
{chr(10).join(f'- {c}' for c in context.get('constraints', {}).get('never', []))}
"""
        else:
            return "No spec context available"

    def planning_phase(self, task: str, context: Dict) -> AgentPlan:
        """
        阶段4：Planning 阶段

        Args:
            task: 用户任务
            context: 上下文字典

        Returns:
            执行计划
        """
        logger.info("=== Phase 4: Planning ===")
        # 简化版：返回空计划
        # 实际实现应该调用 LLM 生成计划
        return AgentPlan()

    def think_phase(self, task: str, context: Dict, observations: list) -> Dict:
        """
        Think 阶段：分析当前状态

        Args:
            task: 用户任务
            context: 上下文字典
            observations: 历史观察

        Returns:
            思考结果（包含 action 和参数）
        """
        logger.info("Think phase")
        # 简化版：返回继续执行的action
        return {"action": "continue", "thought": "Thinking about next step"}

    def act_phase(self, action: Dict) -> Any:
        """
        Act 阶段：执行动作

        Args:
            action: 动作描述

        Returns:
            执行结果
        """
        logger.info("Act phase", action=action.get("action"))
        # 简化版：返回空结果
        return None

    def observe_phase(self, action: Dict, result: Any) -> Dict:
        """
        Observe 阶段：观察执行结果

        Args:
            action: 执行的动作
            result: 执行结果

        Returns:
            观察结果
        """
        logger.info("Observe phase")
        # 简化版：返回空观察
        return {"raw": "Observation", "summary": "Action completed"}

    def reflection_phase(self) -> Dict:
        """
        反思阶段

        Returns:
            反思结果
        """
        logger.info("Reflection phase")
        # 简化版：返回任务未完成
        return {"task_completed": False, "summary": "Task in progress"}

    def check_completion(self, observations: list, manifest) -> bool:
        """
        检查任务是否完成

        Args:
            observations: 观察历史
            manifest: Manifest 对象

        Returns:
            是否完成
        """
        # 简化版：总是返回 False
        return False

    def extract_decisions(self, observations: list) -> list:
        """
        提取决策

        Args:
            observations: 观察历史

        Returns:
            决策列表
        """
        return []

    def extract_artifacts(self, observations: list) -> list:
        """
        提取交付物

        Args:
            observations: 观察历史

        Returns:
            交付物文件列表
        """
        import re
        artifact_files = []
        for obs in observations:
            raw = obs.get("raw", "")
            match = re.search(r'Successfully wrote \d+ chars to (\S+)', raw)
            if match:
                artifact_files.append(match.group(1))
        return artifact_files