"""
领域接口定义

所有业务接口定义，不依赖具体实现
"""

from .interfaces import (
    ILLMClient,
    IContextLoader,
    ISpecGenerator,
    IRouter,
    IManifestManager,
    IPersistenceManager,
    IToolRegistry,
    IConfigManager,
    ICacheManager,
)

__all__ = [
    "ILLMClient",
    "IContextLoader",
    "ISpecGenerator",
    "IRouter",
    "IManifestManager",
    "IPersistenceManager",
    "IToolRegistry",
    "IConfigManager",
    "ICacheManager",
]
