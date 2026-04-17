"""多模型接口 - 支持模型注册和切换"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class ModelTier(Enum):
    """模型层级"""

    LIGHT = "light"
    STANDARD = "standard"
    POWERFUL = "powerful"


@dataclass
class ModelInfo:
    """模型信息"""

    name: str
    tier: ModelTier
    description: str
    max_tokens: int
    cost_per_1k_tokens: float
    capabilities: List[str]


class BaseModelClient:
    """基础模型客户端接口"""

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """同步聊天"""
        raise NotImplementedError

    async def achat(self, messages: List[Dict[str, str]]) -> str:
        """异步聊天"""
        raise NotImplementedError

    def get_model_info(self) -> ModelInfo:
        """获取模型信息"""
        raise NotImplementedError


class ModelRegistry:
    """模型注册表"""

    def __init__(self):
        self.models: Dict[str, BaseModelClient] = {}
        self.model_info: Dict[str, ModelInfo] = {}

    def register(self, name: str, client: BaseModelClient, info: ModelInfo) -> None:
        """注册模型"""
        self.models[name] = client
        self.model_info[name] = info

    def get(self, name: str) -> Optional[BaseModelClient]:
        """获取模型客户端"""
        return self.models.get(name)

    def get_info(self, name: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        return self.model_info.get(name)

    def list_models(self) -> List[str]:
        """列出所有模型"""
        return list(self.models.keys())

    def list_by_tier(self, tier: ModelTier) -> List[str]:
        """按层级列出模型"""
        return [name for name, info in self.model_info.items() if info.tier == tier]

    def get_best_model(
        self,
        tier: Optional[ModelTier] = None,
        capabilities: Optional[List[str]] = None,
    ) -> Optional[str]:
        """获取最佳模型"""
        candidates = list(self.models.keys())

        if tier:
            candidates = [
                name for name in candidates if self.model_info[name].tier == tier
            ]

        if capabilities:
            candidates = [
                name
                for name in candidates
                if all(
                    cap in self.model_info[name].capabilities for cap in capabilities
                )
            ]

        return candidates[0] if candidates else None


class ModelSelector:
    """模型选择器"""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def select_by_complexity(self, complexity: str) -> Optional[BaseModelClient]:
        """根据复杂度选择模型"""
        complexity_mapping = {
            "low": ModelTier.LIGHT,
            "medium": ModelTier.STANDARD,
            "high": ModelTier.POWERFUL,
        }

        tier = complexity_mapping.get(complexity)
        if not tier:
            return None

        model_name = self.registry.get_best_model(tier=tier)
        return self.registry.get(model_name) if model_name else None

    def select_by_cost(self, max_cost: float) -> Optional[BaseModelClient]:
        """根据成本选择模型"""
        candidates = [
            name
            for name, info in self.registry.model_info.items()
            if info.cost_per_1k_tokens <= max_cost
        ]

        if not candidates:
            return None

        best_model = min(
            candidates,
            key=lambda name: self.registry.model_info[name].cost_per_1k_tokens,
        )
        return self.registry.get(best_model)

    def select_by_capability(self, capability: str) -> Optional[BaseModelClient]:
        """根据能力选择模型"""
        model_name = self.registry.get_best_model(capabilities=[capability])
        return self.registry.get(model_name) if model_name else None


# 全局模型注册表
_global_registry = ModelRegistry()


def get_global_registry() -> ModelRegistry:
    """获取全局模型注册表"""
    return _global_registry


def register_model(name: str, client: BaseModelClient, info: ModelInfo) -> None:
    """注册模型到全局注册表"""
    _global_registry.register(name, client, info)


def get_model(name: str) -> Optional[BaseModelClient]:
    """从全局注册表获取模型"""
    return _global_registry.get(name)


def list_models() -> List[str]:
    """列出全局注册表中的所有模型"""
    return _global_registry.list_models()
