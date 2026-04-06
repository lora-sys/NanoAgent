"""
依赖注入容器 - NanoAgent
提供简单的依赖注入功能，支持单例和工厂模式
"""
from typing import Dict, Type, TypeVar, Optional, Callable, Any
from loguru import logger

T = TypeVar('T')


class DIContainer:
    """
    依赖注入容器

    支持两种注册模式：
    1. 单例模式：每次获取返回同一个实例
    2. 工厂模式：每次获取都创建新实例
    """

    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._instances: Dict[Type, Any] = {}

    def register_singleton(self, interface: Type[T], implementation: T):
        """
        注册单例

        Args:
            interface: 接口类型
            implementation: 实现实例
        """
        self._singletons[interface] = implementation
        logger.info(f"✓ Registered singleton: {interface.__name__} -> {type(implementation).__name__}")

    def register_factory(self, interface: Type[T], factory: Callable[[], T]):
        """
        注册工厂

        Args:
            interface: 接口类型
            factory: 工厂函数
        """
        self._factories[interface] = factory
        logger.info(f"✓ Registered factory: {interface.__name__}")

    def get(self, interface: Type[T]) -> T:
        """
        获取依赖

        Args:
            interface: 接口类型

        Returns:
            实现实例

        Raises:
            ValueError: 如果依赖未注册
        """
        # 1. 检查单例
        if interface in self._singletons:
            return self._singletons[interface]

        # 2. 检查工厂
        if interface in self._factories:
            if interface not in self._instances:
                self._instances[interface] = self._factories[interface]()
            return self._instances[interface]

        raise ValueError(f"No implementation registered for {interface.__name__}")

    def resolve(self, interface: Type[T]) -> T:
        """
        解析依赖（别名方法）

        Args:
            interface: 接口类型

        Returns:
            实现实例
        """
        return self.get(interface)

    def has(self, interface: Type[T]) -> bool:
        """
        检查依赖是否已注册

        Args:
            interface: 接口类型

        Returns:
            是否已注册
        """
        return interface in self._singletons or interface in self._factories

    def clear(self):
        """清空所有注册"""
        self._singletons.clear()
        self._factories.clear()
        self._instances.clear()
        logger.info("✓ DI container cleared")


# 全局容器实例
_global_container: Optional[DIContainer] = None


def get_container() -> DIContainer:
    """
    获取全局容器实例

    Returns:
        DIContainer 实例
    """
    global _global_container
    if _global_container is None:
        _global_container = DIContainer()
    return _global_container


def reset_container():
    """重置全局容器"""
    global _global_container
    _global_container = None
    logger.info("✓ Global DI container reset")


def configure_container(config: Callable[[DIContainer], None]):
    """
    配置全局容器

    Args:
        config: 配置函数
    """
    container = get_container()
    config(container)


def inject(interface: Type[T]) -> T:
    """
    依赖注入装饰器（函数注入）

    Args:
        interface: 接口类型

    Returns:
        依赖实例
    """
    return get_container().get(interface)