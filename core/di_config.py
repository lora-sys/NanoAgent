"""
依赖注入配置 - NanoAgent
配置所有组件的依赖关系（配置驱动架构）
"""

from core.container import DIContainer
from core.config import ConfigManager, get_config_manager
from core.llm_client import NanoLLMClient
from core.router import HybridRouter
from core.manifest_manager import ManifestManager
from spec.context import ContextLoader
from spec.generator import SpecGenerator
from core.persistence import PersistenceManager
from core.tools.registry import ToolRegistry
from core.cache import CacheManager
from core.executor import AgentExecutor
from core.agent_state import AgentState
from core.spec_initializer import SpecInitializer

# 导入接口（用于类型提示，实际注册具体实现）
from core.interfaces import (
    ILLMClient,
    IRouter,
    IManifestManager,
    IContextLoader,
    ISpecGenerator,
    IPersistenceManager,
)


def setup_dependencies(container: DIContainer, config: dict = None, model: str = None):
    """
    设置依赖关系（配置驱动）

    Args:
        container: DI 容器实例
        config: 配置字典（可选）
        model: LLM 模型名称（可选，用于向后兼容）
    """

    # 1. 配置管理器（单例）
    if config:
        # 使用传入的配置创建配置管理器
        config_manager = MockConfigManager(config)
    else:
        # 使用默认的配置管理器
        config_manager = get_config_manager()

    container.register(ConfigManager, instance=config_manager)

    # 读取配置
    core_config = config_manager.get_module_config("core")
    llm_config = config_manager.get_module_config("llm")
    tools_config = config_manager.get_module_config("tools")

    # 2. LLM 客户端（单例）
    llm_model = model or llm_config.get("default", {}).get(
        "model", "openai/qwen3.5-plus"
    )
    llm_client = NanoLLMClient(model=llm_model, config=llm_config)
    container.register_singleton(ILLMClient, llm_client)

    # 3. 路由器（单例）
    router = HybridRouter(llm_client)
    container.register_singleton(IRouter, router)

    # 4. Manifest 管理器（单例）
    manifest_manager = ManifestManager()
    container.register_singleton(IManifestManager, manifest_manager)

    # 5. 上下文加载器（单例）
    context_loader = ContextLoader(manifest_manager)
    container.register_singleton(IContextLoader, context_loader)

    # 6. Spec 生成器（单例）
    spec_generator = SpecGenerator(llm_client)
    container.register_singleton(ISpecGenerator, spec_generator)

    # 7. 持久化管理器（单例）
    persistence_manager = PersistenceManager()
    container.register_singleton(IPersistenceManager, persistence_manager)

    # 8. 工具注册表（单例）
    tool_registry = ToolRegistry(tools_config)
    container.register(ToolRegistry, instance=tool_registry)

    # 9. 缓存管理器（单例）
    cache_config = config_manager.get_module_config("cache")
    storage_config = cache_config.get("storage", {})
    cache_dir = storage_config.get("cache_dir", ".cache")
    ttl_hours = storage_config.get("default_ttl_hours", 24)
    cache_manager = CacheManager(cache_dir=cache_dir, ttl_hours=ttl_hours)
    container.register(CacheManager, instance=cache_manager)

    # 10. 状态管理器（单例）
    state = AgentState(core_config)
    container.register(AgentState, instance=state)

    # 11. Spec初始化器（单例）
    spec_initializer = SpecInitializer(llm_client=llm_client)  # 传入已有的 llm 客户端
    container.register(SpecInitializer, instance=spec_initializer)

    # 12. 执行器（单例）
    executor = AgentExecutor(
        llm_client=llm_client,
        router=router,
        manifest_manager=manifest_manager,
        context_loader=context_loader,
        spec_generator=spec_generator,
        tool_registry=tool_registry,
        persistence_manager=persistence_manager,
        cache=cache_manager,
        config=config_manager.get_main_config(),
        state=state,  # 传入 state
    )
    container.register(AgentExecutor, instance=executor)


def initialize_container(config: dict = None, model: str = None) -> DIContainer:
    """
    初始化并配置全局容器（配置驱动）

    Args:
        config: 配置字典（可选）
        model: LLM 模型名称（可选，用于向后兼容）

    Returns:
        配置好的 DI 容器
    """
    from core.container import get_container, reset_container

    # 重置容器（如果已存在）
    reset_container()

    # 获取新容器
    container = get_container()

    # 配置依赖
    setup_dependencies(container, config, model)

    return container


class MockConfigManager:
    """模拟配置管理器，用于直接传入配置字典"""

    def __init__(self, config: dict):
        self.config = config

    def get_module_config(self, module_name: str) -> dict:
        """获取模块配置"""
        return self.config.get(module_name, {})

    def get_main_config(self) -> dict:
        """获取主配置"""
        return self.config.get("main", self.config)
