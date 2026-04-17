"""可组合模块 - 灵活拼装各种功能"""

from typing import Any, Dict, Optional

from core.router import Router
from core.chain import PromptChain
from core.agent import NanoAgent
from core.model_interface import ModelRegistry, ModelSelector, get_global_registry


class ComposableAgent:
    """可组合的 Agent - 支持灵活拼装各种功能"""

    def __init__(
        self,
        base_agent: Optional[NanoAgent] = None,
        router: Optional[Router] = None,
        chain: Optional[PromptChain] = None,
        model_registry: Optional[ModelRegistry] = None,
    ):
        """
        初始化可组合 Agent

        Args:
            base_agent: 基础 Agent
            router: 路由器
            chain: 提示链
            model_registry: 模型注册表
        """
        self.base_agent = base_agent or NanoAgent()
        self.router = router
        self.chain = chain
        self.model_registry = model_registry or get_global_registry()
        self.model_selector = ModelSelector(self.model_registry)
        self.features: Dict[str, Any] = {}

    def add_feature(self, name: str, feature: Any) -> "ComposableAgent":
        """添加功能模块"""
        self.features[name] = feature
        return self

    def add_router(self, router: Router) -> "ComposableAgent":
        """添加路由器"""
        self.router = router
        return self

    def add_chain(self, chain: PromptChain) -> "ComposableAgent":
        """添加提示链"""
        self.chain = chain
        return self

    def set_model_registry(self, registry: ModelRegistry) -> "ComposableAgent":
        """设置模型注册表"""
        self.model_registry = registry
        self.model_selector = ModelSelector(registry)
        return self

    async def _select_model(self, complexity: str) -> Optional[str]:
        """选择模型"""
        selected_model = self.model_selector.select_by_complexity(complexity)
        return selected_model.get_model_info().name if selected_model else None

    async def _route_task(self, task: str) -> Dict[str, Any]:
        """路由任务"""
        if hasattr(self.router, "route"):
            decision = await self.router.route(task)
        else:
            decision = self.router.route_sync(task)
        return decision.to_dict()

    async def _chain_execute(self, task: str) -> Any:
        """执行提示链"""
        if hasattr(self.chain, "run"):
            return await self.chain.run(task, self.base_agent.llm)
        return self.chain.run_sync(task, self.base_agent.llm)

    async def _base_execute(self, task: str, **kwargs) -> Dict[str, Any]:
        """基础 Agent 执行"""
        return self.base_agent.run(task, **kwargs)

    async def execute(
        self,
        task: str,
        use_router: bool = False,
        use_chain: bool = False,
        use_model_selection: bool = False,
        complexity: str = "medium",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        执行任务

        Args:
            task: 任务描述
            use_router: 是否使用路由器
            use_chain: 是否使用提示链
            use_model_selection: 是否使用模型选择
            complexity: 任务复杂度 (low/medium/high)
            **kwargs: 其他参数

        Returns:
            执行结果
        """
        result = {
            "task": task,
            "features_used": [],
            "execution_path": [],
        }

        # 1. 模型选择阶段
        if use_model_selection:
            result["execution_path"].append("model_selection")
            result["features_used"].append("model_selection")
            result["selected_model"] = await self._select_model(complexity)

        # 2. 路由阶段
        if use_router and self.router:
            result["execution_path"].append("routing")
            result["features_used"].append("router")
            result["routing_decision"] = await self._route_task(task)

        # 3. 提示链阶段
        if use_chain and self.chain:
            result["execution_path"].append("chaining")
            result["features_used"].append("chain")
            result["chain_result"] = await self._chain_execute(task)

        # 4. 基础 Agent 阶段
        if not use_router and not use_chain:
            result["execution_path"].append("base_agent")
            result["features_used"].append("base_agent")
            result["agent_result"] = await self._base_execute(task, **kwargs)

        return result

    def execute_sync(
        self,
        task: str,
        use_router: bool = False,
        use_chain: bool = False,
        use_model_selection: bool = False,
        complexity: str = "medium",
        **kwargs,
    ) -> Dict[str, Any]:
        """同步执行任务"""
        import asyncio

        return asyncio.run(
            self.execute(
                task, use_router, use_chain, use_model_selection, complexity, **kwargs
            )
        )


class AgentBuilder:
    """Agent 构建器 - 提供流式 API 构建 Agent"""

    def __init__(self):
        self.agent = ComposableAgent()

    def with_base_agent(self, agent: NanoAgent) -> "AgentBuilder":
        """设置基础 Agent"""
        self.agent.base_agent = agent
        return self

    def with_router(self, router: Router) -> "AgentBuilder":
        """添加路由器"""
        self.agent.add_router(router)
        return self

    def with_chain(self, chain: PromptChain) -> "AgentBuilder":
        """添加提示链"""
        self.agent.add_chain(chain)
        return self

    def with_feature(self, name: str, feature: Any) -> "AgentBuilder":
        """添加自定义功能"""
        self.agent.add_feature(name, feature)
        return self

    def with_model_registry(self, registry: ModelRegistry) -> "AgentBuilder":
        """设置模型注册表"""
        self.agent.set_model_registry(registry)
        return self

    def build(self) -> ComposableAgent:
        """构建 Agent"""
        return self.agent
