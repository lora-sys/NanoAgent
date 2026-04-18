"""路由模块 - 智能任务分发和路由"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union

from core.context import RouteContext


@dataclass
class RouteDecision:
    """路由决策结果"""

    target: str
    reasoning: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass
class Route:
    """路由规则"""

    name: str
    target: str
    condition: Union[str, Callable[[str], bool]]
    priority: int = 0
    description: str = ""

    def matches(self, task: str) -> bool:
        if isinstance(self.condition, str):
            return self.condition.lower() in task.lower()
        elif callable(self.condition):
            return self.condition(task)
        return False


class Router:
    """智能路由器 - 任务分发和路由决策"""

    def __init__(
        self,
        name: str = "default_router",
        default_target: str = "default",
        use_llm_routing: bool = False,
    ):
        """
        初始化路由器

        Args:
            name: 路由器名称
            default_target: 默认目标处理器
            use_llm_routing: 是否使用 LLM 智能路由
        """
        self.name = name
        self.routes: List[Route] = []
        self.default_target = default_target
        self.use_llm_routing = use_llm_routing
        self.llm_client: Optional[Any] = None

    def add_route(
        self,
        name: str,
        target: str,
        condition: Union[str, Callable[[str], bool]],
        priority: int = 0,
        description: str = "",
    ) -> "Router":
        """
        添加路由规则

        Args:
            name: 路由名称
            target: 目标处理器
            condition: 路由条件（关键词或函数）
            priority: 优先级（数字越大优先级越高）
            description: 路由描述

        Returns:
            self，支持链式调用
        """
        route = Route(name, target, condition, priority, description)
        self.routes.append(route)
        # 按优先级排序
        self.routes.sort(key=lambda r: r.priority, reverse=True)
        return self

    def set_llm_client(self, llm_client: Any) -> None:
        """设置 LLM 客户端用于智能路由"""
        self.llm_client = llm_client

    def _route_by_keywords(self, task: str) -> Optional[RouteDecision]:
        """基于关键词路由"""
        for route in self.routes:
            if route.matches(task):
                return RouteDecision(
                    target=route.target,
                    reasoning=f"关键词匹配: {route.name}",
                    confidence=1.0,
                    metadata={"route_name": route.name, "route_type": "keyword"},
                )
        return None

    async def _route_by_llm(self, task: str) -> Optional[RouteDecision]:
        """基于 LLM 智能路由"""
        if not self.llm_client or not self.use_llm_routing:
            return None

        # 构建路由提示
        targets = [route.target for route in self.routes] + [self.default_target]

        prompt = f"""请将以下任务路由到最合适的目标处理器。

可用目标: {", ".join(targets)}

任务: {task}

请以 JSON 格式返回路由决策:
{{
    "target": "目标处理器名称",
    "reasoning": "路由原因",
    "confidence": 0.0-1.0
}}"""

        try:
            # 调用 LLM（优先异步）
            if hasattr(self.llm_client, "achat") and asyncio.iscoroutinefunction(
                self.llm_client.achat
            ):
                response = await self.llm_client.achat(
                    [{"role": "user", "content": prompt}]
                )
            else:
                response = self.llm_client.chat([{"role": "user", "content": prompt}])

            # 解析响应
            decision_data = json.loads(response)
            target = decision_data.get("target", self.default_target)

            # 验证目标是否有效
            if target not in targets:
                target = self.default_target

            return RouteDecision(
                target=target,
                reasoning=decision_data.get("reasoning", "LLM 智能路由"),
                confidence=float(decision_data.get("confidence", 0.8)),
                metadata={"route_type": "llm", "raw_response": response},
            )

        except (json.JSONDecodeError, ValueError, KeyError):
            # 解析失败
            return None
        except Exception:
            # LLM 调用失败
            return None

    async def route(
        self,
        task: str,
        context: Optional[RouteContext] = None,
    ) -> RouteDecision:
        """
        执行路由决策

        Args:
            task: 任务描述
            context: 路由上下文

        Returns:
            路由决策结果
        """
        # 初始化上下文
        if context is None:
            context = RouteContext()

        # 1. 尝试关键词路由（快速）
        decision = self._route_by_keywords(task)

        # 2. 如果关键词路由失败且启用 LLM 路由，尝试智能路由
        if decision is None and self.use_llm_routing:
            decision = await self._route_by_llm(task)

        # 3. 如果都失败，使用默认路由
        if decision is None:
            decision = RouteDecision(
                target=self.default_target,
                reasoning="使用默认路由",
                confidence=0.5,
                metadata={"route_type": "default"},
            )

        # 添加历史记录
        context.add_history(decision, task)

        return decision

    def route_sync(
        self,
        task: str,
        context: Optional[RouteContext] = None,
    ) -> RouteDecision:
        """同步路由决策"""
        return asyncio.run(self.route(task, context))

    def get_route_info(self) -> Dict[str, Any]:
        """获取路由器信息"""
        return {
            "name": self.name,
            "route_count": len(self.routes),
            "default_target": self.default_target,
            "use_llm_routing": self.use_llm_routing,
            "routes": [
                {
                    "name": route.name,
                    "target": route.target,
                    "priority": route.priority,
                    "description": route.description,
                }
                for route in self.routes
            ],
        }


def create_simple_router() -> Router:
    """创建简单路由器（仅关键词路由）"""
    router = Router("simple_router", default_target="general")
    return router


def create_smart_router(default_target: str = "general") -> Router:
    """创建智能路由器（支持 LLM 路由）"""
    router = Router("smart_router", default_target=default_target, use_llm_routing=True)
    return router
