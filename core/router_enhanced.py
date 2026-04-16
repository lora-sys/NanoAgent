"""增强路由模块 - 支持门控机制和多模型路由"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class RouteDecision:
    """路由决策结果"""

    target: str
    reasoning: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    gate_check: Optional[Callable[[str], bool]] = None  # 门控检查函数

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
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
    model_preference: Optional[str] = None  # 模型偏好
    gate_check: Optional[Callable[[str], bool]] = None  # 门控检查

    def matches(self, task: str) -> bool:
        """检查任务是否匹配此路由"""
        if isinstance(self.condition, str):
            return self.condition.lower() in task.lower()
        elif callable(self.condition):
            return self.condition(task)
        return False

    def validate_gate(self, task: str) -> bool:
        """验证门控条件"""
        if self.gate_check is None:
            return True
        return self.gate_check(task)


class EnhancedRouter:
    """增强路由器 - 支持门控机制和多模型路由"""

    def __init__(
        self,
        name: str = "enhanced_router",
        default_target: str = "default",
        use_llm_routing: bool = False,
        enable_gate: bool = True,
    ):
        """
        初始化增强路由器

        Args:
            name: 路由器名称
            default_target: 默认目标处理器
            use_llm_routing: 是否使用 LLM 智能路由
            enable_gate: 是否启用门控机制
        """
        self.name = name
        self.routes: List[Route] = []
        self.default_target = default_target
        self.use_llm_routing = use_llm_routing
        self.enable_gate = enable_gate
        self.llm_client: Optional[Any] = None
        self.model_registry: Dict[str, Any] = {}  # 模型注册表

    def add_route(
        self,
        name: str,
        target: str,
        condition: Union[str, Callable[[str], bool]],
        priority: int = 0,
        description: str = "",
        model_preference: Optional[str] = None,
        gate_check: Optional[Callable[[str], bool]] = None,
    ) -> "EnhancedRouter":
        """
        添加路由规则

        Args:
            name: 路由名称
            target: 目标处理器
            condition: 路由条件（关键词或函数）
            priority: 优先级（数字越大优先级越高）
            description: 路由描述
            model_preference: 模型偏好（如 "haiku", "sonnet"）
            gate_check: 门控检查函数

        Returns:
            self，支持链式调用
        """
        route = Route(
            name,
            target,
            condition,
            priority,
            description,
            model_preference,
            gate_check,
        )
        self.routes.append(route)
        self.routes.sort(key=lambda r: r.priority, reverse=True)
        return self

    def register_model(self, model_name: str, model_client: Any) -> None:
        """注册模型"""
        self.model_registry[model_name] = model_client

    def set_llm_client(self, llm_client: Any) -> None:
        """设置默认 LLM 客户端"""
        self.llm_client = llm_client

    def _route_by_keywords(self, task: str) -> Optional[RouteDecision]:
        """基于关键词路由"""
        for route in self.routes:
            if route.matches(task):
                # 检查门控条件
                if self.enable_gate and not route.validate_gate(task):
                    continue

                return RouteDecision(
                    target=route.target,
                    reasoning=f"关键词匹配: {route.name}",
                    confidence=1.0,
                    metadata={
                        "route_name": route.name,
                        "route_type": "keyword",
                        "model_preference": route.model_preference,
                    },
                    gate_check=route.gate_check,
                )
        return None

    async def _route_by_llm(self, task: str) -> Optional[RouteDecision]:
        """基于 LLM 智能路由"""
        if not self.llm_client or not self.use_llm_routing:
            return None

        targets = [route.target for route in self.routes] + [self.default_target]

        prompt = f"""请将以下任务路由到最合适的目标处理器。

可用目标: {", ".join(targets)}

任务: {task}

请以 JSON 格式返回路由决策:
{{
    "target": "目标处理器名称",
    "reasoning": "路由原因",
    "confidence": 0.0-1.0,
    "complexity": "low|medium|high"
}}"""

        try:
            if hasattr(self.llm_client, "achat") and asyncio.iscoroutinefunction(
                self.llm_client.achat
            ):
                response = await self.llm_client.achat(
                    [{"role": "user", "content": prompt}]
                )
            else:
                response = self.llm_client.chat([{"role": "user", "content": prompt}])

            decision_data = json.loads(response)
            target = decision_data.get("target", self.default_target)
            complexity = decision_data.get("complexity", "medium")

            if target not in targets:
                target = self.default_target

            # 根据复杂度选择模型
            model_preference = self._select_model_by_complexity(complexity)

            return RouteDecision(
                target=target,
                reasoning=decision_data.get("reasoning", "LLM 智能路由"),
                confidence=float(decision_data.get("confidence", 0.8)),
                metadata={
                    "route_type": "llm",
                    "complexity": complexity,
                    "model_preference": model_preference,
                    "raw_response": response,
                },
            )

        except (json.JSONDecodeError, ValueError, KeyError):
            return None
        except Exception:
            return None

    def _select_model_by_complexity(self, complexity: str) -> str:
        """根据复杂度选择模型"""
        complexity_mapping = {
            "low": "haiku",  # 简单任务用小模型
            "medium": "sonnet",  # 中等任务用中等模型
            "high": "opus",  # 复杂任务用大模型
        }
        return complexity_mapping.get(complexity, "sonnet")

    async def route(
        self,
        task: str,
        context: Optional[Any] = None,
    ) -> RouteDecision:
        """
        执行路由决策

        Args:
            task: 任务描述
            context: 路由上下文

        Returns:
            路由决策结果
        """
        # 1. 尝试关键词路由
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

        return decision

    def get_model_for_decision(self, decision: RouteDecision) -> Any:
        """根据路由决策获取对应的模型"""
        model_preference = decision.metadata.get("model_preference")

        if model_preference and model_preference in self.model_registry:
            return self.model_registry[model_preference]

        return self.llm_client


def create_customer_service_router() -> EnhancedRouter:
    """创建客户服务路由器（示例）"""

    # 门控检查函数
    def is_refund_related(task: str) -> bool:
        """检查是否与退款相关"""
        keywords = ["退款", "退钱", "退货", "refund"]
        return any(kw in task for kw in keywords)

    def is_technical_issue(task: str) -> bool:
        """检查是否是技术问题"""
        keywords = ["bug", "错误", "故障", "技术", "technical"]
        return any(kw in task for kw in keywords)

    router = EnhancedRouter(
        "customer_service", default_target="general", enable_gate=True
    )

    router.add_route(
        name="退款处理",
        target="refund_service",
        condition="退款",
        priority=10,
        description="处理退款相关请求",
        model_preference="haiku",  # 简单任务用小模型
        gate_check=is_refund_related,
    ).add_route(
        name="技术支持",
        target="technical_support",
        condition="技术",
        priority=8,
        description="处理技术支持请求",
        model_preference="sonnet",  # 中等复杂度
        gate_check=is_technical_issue,
    ).add_route(
        name="一般咨询",
        target="general_service",
        condition="咨询",
        priority=5,
        description="处理一般性咨询",
        model_preference="haiku",
    )

    return router
