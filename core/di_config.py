"""
依赖注入配置 - NanoAgent
配置所有组件的依赖关系
"""
from core.container import DIContainer
from core.llm_client import NanoLLMClient
from core.router import HybridRouter
from core.manifest_manager import ManifestManager
from spec.context import ContextLoader
from spec.generator import SpecGenerator
from core.persistence import PersistenceManager
from core.tools.registry import ToolRegistry
from core.cache import CacheManager

# 导入接口（用于类型提示，实际注册具体实现）
from core.interfaces import (
    ILLMClient, IRouter, IManifestManager,
    IContextLoader, ISpecGenerator, IPersistenceManager
)


def setup_dependencies(container: DIContainer, model: str = "openai/qwen3.5-plus"):
    """
    设置依赖关系

    Args:
        container: DI 容器实例
        model: LLM 模型名称
    """

    # 1. LLM 客户端（单例）
    llm_client = NanoLLMClient(model)
    container.register_singleton(ILLMClient, llm_client)

    # 2. 路由器（单例）
    router = HybridRouter(llm_client)
    container.register_singleton(IRouter, router)

    # 3. Manifest 管理器（单例）
    manifest_manager = ManifestManager()
    container.register_singleton(IManifestManager, manifest_manager)

    # 4. 上下文加载器（单例）
    context_loader = ContextLoader(manifest_manager)
    container.register_singleton(IContextLoader, context_loader)

    # 5. Spec 生成器（单例）
    spec_generator = SpecGenerator(llm_client)
    container.register_singleton(ISpecGenerator, spec_generator)

    # 6. 持久化管理器（单例）
    persistence_manager = PersistenceManager()
    container.register_singleton(IPersistenceManager, persistence_manager)

    # 7. 工具注册表（单例）
    # 导入 agent_loop 中的 ToolRegistry 包装类
    from core.agent_loop import ToolRegistry as AgentToolRegistry
    tool_registry = AgentToolRegistry()
    container.register_singleton(AgentToolRegistry, tool_registry)

    # 8. 缓存管理器（单例）
    cache_manager = CacheManager()
    container.register_singleton(CacheManager, cache_manager)


def initialize_container(model: str = "openai/qwen3.5-plus") -> DIContainer:
    """
    初始化并配置全局容器

    Args:
        model: LLM 模型名称

    Returns:
        配置好的 DI 容器
    """
    from core.container import get_container, reset_container

    # 重置容器（如果已存在）
    reset_container()

    # 获取新容器
    container = get_container()

    # 配置依赖
    setup_dependencies(container, model)

    return container