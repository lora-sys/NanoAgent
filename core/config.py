"""
配置管理器 - NanoAgent
提供统一的配置加载和访问接口
"""
import os
import toml
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger


class ConfigManager:
    """配置管理器 - 负责加载和管理所有模块配置"""
    
    def __init__(self, config_dir: str = "config", main_config: str = "nanoagent.toml"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
            main_config: 主配置文件路径
        """
        self.config_dir = Path(config_dir)
        self.main_config_path = Path(main_config)
        self.main_config: Dict[str, Any] = {}
        self.module_configs: Dict[str, Dict[str, Any]] = {}
        
        # 加载配置
        self._load_configs()
        
    def _load_configs(self):
        """加载所有配置文件"""
        try:
            # 加载主配置
            self.main_config = self._load_toml_file(self.main_config_path)
            logger.info(f"✓ 加载主配置: {self.main_config_path}")
            
            # 加载模块配置
            modules = self.main_config.get("modules", {})
            for module_name, config_path in modules.items():
                try:
                    self.module_configs[module_name] = self._load_toml_file(config_path)
                    logger.info(f"✓ 加载模块配置: {module_name} -> {config_path}")
                except Exception as e:
                    logger.warning(f"⚠️  加载模块配置失败: {module_name} ({config_path}): {e}")
                    self.module_configs[module_name] = {}
                    
        except Exception as e:
            logger.error(f"❌ 加载配置失败: {e}")
            # 使用默认配置
            self._set_default_configs()
    
    def _load_toml_file(self, file_path: str) -> Dict[str, Any]:
        """
        加载 TOML 文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            配置字典
        """
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"配置文件不存在: {file_path}")
            return {}
        
        with open(path, 'r', encoding='utf-8') as f:
            config = toml.load(f)
        
        # 替换环境变量
        return self._resolve_env_vars(config)
    
    def _resolve_env_vars(self, config: Any) -> Any:
        """
        递归解析配置中的环境变量
        
        Args:
            config: 配置对象
            
        Returns:
            解析后的配置
        """
        if isinstance(config, str):
            # 检查是否是环境变量引用 ${VAR_NAME}
            if config.startswith("${") and config.endswith("}"):
                var_name = config[2:-1]
                return os.getenv(var_name, config)
            return config
        elif isinstance(config, dict):
            return {key: self._resolve_env_vars(value) for key, value in config.items()}
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        else:
            return config
    
    def _set_default_configs(self):
        """设置默认配置"""
        self.main_config = {
            "general": {
                "version": "1.0.0",
                "environment": "development",
                "debug": False
            },
            "modules": {}
        }
        self.module_configs = {}
    
    def get(self, module: str, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        Args:
            module: 模块名称
            key: 配置键（支持点号分隔的嵌套键）
            default: 默认值
            
        Returns:
            配置值
        """
        config = self.module_configs.get(module, {})
        
        # 支持嵌套键访问，如 "logging.level"
        keys = key.split(".")
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_module_config(self, module: str) -> Dict[str, Any]:
        """
        获取整个模块配置
        
        Args:
            module: 模块名称
            
        Returns:
            模块配置字典
        """
        return self.module_configs.get(module, {})
    
    def get_main_config(self) -> Dict[str, Any]:
        """获取主配置"""
        return self.main_config
    
    def reload(self):
        """重新加载所有配置"""
        logger.info("重新加载配置...")
        self._load_configs()
    
    def validate(self) -> bool:
        """
        验证配置的有效性
        
        Returns:
            配置是否有效
        """
        # 检查必需的模块
        required_modules = ["core", "llm", "cache"]
        for module in required_modules:
            if module not in self.module_configs:
                logger.warning(f"缺少必需的模块配置: {module}")
                return False
        
        # 检查必需的配置项
        llm_config = self.get_module_config("llm")
        if "clients" not in llm_config or not llm_config["clients"]:
            logger.error("LLM 配置缺少客户端配置")
            return False
        
        return True
    
    def __repr__(self) -> str:
        return f"ConfigManager(modules={list(self.module_configs.keys())})"


# 全局配置管理器实例
_global_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_dir: str = "config", main_config: str = "nanoagent.toml") -> ConfigManager:
    """
    获取全局配置管理器实例（单例模式）
    
    Args:
        config_dir: 配置目录
        main_config: 主配置文件
        
    Returns:
        配置管理器实例
    """
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager(config_dir, main_config)
    return _global_config_manager


def reset_config_manager():
    """重置全局配置管理器（主要用于测试）"""
    global _global_config_manager
    _global_config_manager = None