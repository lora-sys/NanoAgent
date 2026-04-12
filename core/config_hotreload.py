"""
配置热更新支持

实现配置观察者模式，支持配置变更通知和自动重载
"""

from typing import Dict, Any, Callable, List, Optional
from pathlib import Path
import time
import threading
from loguru import logger


class ConfigObserver:
    """配置观察者接口"""
    
    def on_config_changed(self, key: str, old_value: Any, new_value: Any):
        """
        配置变更回调
        
        Args:
            key: 变更的配置键
            old_value: 旧值
            new_value: 新值
        """
        pass


class ConfigWatcher:
    """配置文件监视器
    
    监视配置文件变化，自动通知观察者
    """
    
    def __init__(self, config_dir: str = "config", poll_interval: float = 1.0):
        """
        初始化监视器
        
        Args:
            config_dir: 配置目录
            poll_interval: 轮询间隔（秒）
        """
        self.config_dir = Path(config_dir)
        self.poll_interval = poll_interval
        self._observers: List[ConfigObserver] = []
        self._file_hashes: Dict[str, str] = {}
        self._watching = False
        self._thread: Optional[threading.Thread] = None
    
    def add_observer(self, observer: ConfigObserver):
        """添加观察者"""
        self._observers.append(observer)
        logger.info(f"✓ Added config observer: {type(observer).__name__}")
    
    def remove_observer(self, observer: ConfigObserver):
        """移除观察者"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def start_watching(self):
        """开始监视"""
        if self._watching:
            return
        
        self._watching = True
        self._file_hashes = self._compute_all_hashes()
        
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        logger.info(f"✓ Config watcher started (interval: {self.poll_interval}s)")
    
    def stop_watching(self):
        """停止监视"""
        self._watching = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("✓ Config watcher stopped")
    
    def _watch_loop(self):
        """监视循环"""
        while self._watching:
            try:
                self._check_for_changes()
                time.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Config watch error: {e}")
    
    def _check_for_changes(self):
        """检查配置变化"""
        current_hashes = self._compute_all_hashes()
        
        for file_path, current_hash in current_hashes.items():
            old_hash = self._file_hashes.get(file_path)
            if old_hash != current_hash:
                logger.info(f"Config file changed: {file_path}")
                self._notify_observers(file_path)
                self._file_hashes[file_path] = current_hash
    
    def _compute_all_hashes(self) -> Dict[str, str]:
        """计算所有配置文件的哈希"""
        import hashlib
        
        hashes = {}
        if self.config_dir.exists():
            for toml_file in self.config_dir.glob("*.toml"):
                content = toml_file.read_bytes()
                hashes[str(toml_file)] = hashlib.md5(content).hexdigest()
        
        return hashes
    
    def _notify_observers(self, changed_file: str):
        """通知所有观察者"""
        for observer in self._observers:
            try:
                observer.on_config_changed(changed_file, None, None)
            except Exception as e:
                logger.error(f"Observer notification failed: {e}")


class HotReloadableConfig:
    """支持热重载的配置管理器"""
    
    def __init__(self, config_manager, auto_reload: bool = True, poll_interval: float = 1.0):
        """
        初始化热重载配置
        
        Args:
            config_manager: ConfigManager 实例
            auto_reload: 是否自动重载
            poll_interval: 轮询间隔
        """
        self.config_manager = config_manager
        self.watcher = ConfigWatcher(
            config_dir=str(config_manager.config_dir),
            poll_interval=poll_interval
        )
        
        if auto_reload:
            self.watcher.add_observer(self)
            self.watcher.start_watching()
    
    def on_config_changed(self, key: str, old_value: Any, new_value: Any):
        """配置变更回调"""
        logger.info("Reloading configuration...")
        try:
            self.config_manager._load_configs()
            logger.info("✓ Configuration reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config_manager.get(key, default)
    
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """获取模块配置"""
        return self.config_manager.get_module_config(module_name)
    
    def stop(self):
        """停止热重载"""
        self.watcher.stop_watching()
