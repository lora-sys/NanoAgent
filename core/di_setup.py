"""
依赖注入配置

统一注册所有单例到 DI Container
消除全局状态混乱
"""

from typing import Optional
from loguru import logger
from infrastructure.container import DIContainer, get_container
from infrastructure.config.manager import ConfigManager
from infrastructure.cache.manager import CacheManager
from infrastructure.tools.registry import ToolRegistry
from domain.interfaces.interfaces import (
    IConfigManager,
    ICacheManager,
    IToolRegistry,
)


def setup_dependency_injection(
    container: Optional[DIContainer] = None,
    config_dir: str = "config",
    main_config: str = "nanoagent.toml",
) -> DIContainer:
    """
    设置依赖注入
    
    统一注册所有单例，消除全局状态
    
    Args:
        container: DI 容器实例（可选，默认使用全局）
        config_dir: 配置目录
        main_config: 主配置文件
        
    Returns:
        配置好的 DI 容器
    """
    if container is None:
        container = get_container()
    
    # 1. 注册配置管理器
    config_manager = ConfigManager(config_dir, main_config)
    container.register_singleton(IConfigManager, config_manager)
    
    # 2. 注册缓存管理器
    cache_manager = CacheManager()
    container.register_singleton(ICacheManager, cache_manager)
    
    # 3. 注册工具注册表
    tools_config = config_manager.get_module_config("tools")
    tool_registry = ToolRegistry(tools_config)
    container.register_singleton(IToolRegistry, tool_registry)
    
    logger.info("✓ Dependency injection setup complete")
    logger.info(f"  - ConfigManager: {IConfigManager.__name__}")
    logger.info(f"  - CacheManager: {ICacheManager.__name__}")
    logger.info(f"  - ToolRegistry: {IToolRegistry.__name__}")
    
    return container


def get_config() -> ConfigManager:
    """获取配置管理器（通过 DI）"""
    return get_container().get(IConfigManager)


def get_cache() -> CacheManager:
    """获取缓存管理器（通过 DI）"""
    return get_container().get(ICacheManager)


def get_tool_registry() -> ToolRegistry:
    """获取工具注册表（通过 DI）"""
    return get_container().get(IToolRegistry)
