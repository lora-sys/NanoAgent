"""
缓存管理器 - NanoAgent
提供 LLM 调用缓存和结果缓存
"""

import hashlib
import json
import os
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
from loguru import logger
from infrastructure.config.manager import get_config_manager


class CacheManager:
    """缓存管理器"""

    def __init__(self, cache_dir: Optional[str] = None, ttl_hours: int = None):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录
            ttl_hours: 缓存过期时间（小时）
        """
        # 从配置文件读取参数
        config = get_config_manager()
        cache_config = config.get_module_config("cache")

        # 优先使用传入参数，其次使用配置文件，最后使用默认值
        if cache_dir is None:
            cache_dir = cache_config.get("storage", {}).get("cache_dir", None)
            if cache_dir is None:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                cache_dir = os.path.join(base_dir, ".cache")

        if ttl_hours is None:
            ttl_hours = cache_config.get("storage", {}).get("default_ttl_hours", 24)

        self.cache_dir = cache_dir
        self.ttl_hours = ttl_hours

        # 读取缓存配置
        self.llm_cache_enabled = cache_config.get("llm_cache", {}).get("enabled", True)
        self.include_model_name = cache_config.get("llm_cache", {}).get(
            "include_model_name", True
        )
        self.key_hash_algorithm = cache_config.get("llm_cache", {}).get(
            "key_hash_algorithm", "sha256"
        )

        os.makedirs(cache_dir, exist_ok=True)
        logger.info(
            f"Initialized CacheManager with dir: {cache_dir}, ttl: {ttl_hours}h, hash: {self.key_hash_algorithm}"
        )

    def _get_cache_key(self, messages: list, **kwargs) -> str:
        """生成缓存键"""
        # 将消息和参数转换为字符串
        cache_data = {"messages": messages, "kwargs": kwargs}

        # 如果需要包含模型名称，添加到缓存数据中
        if self.include_model_name and "model" in kwargs:
            cache_data["model"] = kwargs["model"]

        cache_str = json.dumps(cache_data, sort_keys=True)

        # 使用配置的哈希算法
        try:
            hash_obj = hashlib.new(self.key_hash_algorithm)
            hash_obj.update(cache_str.encode())
            return hash_obj.hexdigest()
        except ValueError:
            # 如果算法不支持，回退到 md5
            logger.warning(
                f"Unsupported hash algorithm: {self.key_hash_algorithm}, falling back to md5"
            )
            return hashlib.md5(cache_str.encode()).hexdigest()

    def _get_cache_file(self, cache_key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")

    def _is_cache_valid(self, cache_file: str) -> bool:
        """检查缓存是否有效"""
        if not os.path.exists(cache_file):
            return False

        # 检查文件修改时间
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        expiry_time = datetime.now() - timedelta(hours=self.ttl_hours)

        return file_time > expiry_time

    def get(self, messages: list, **kwargs) -> Optional[Any]:
        """
        从缓存获取结果

        Args:
            messages: 消息列表
            **kwargs: 其他参数

        Returns:
            缓存的结果，如果不存在或已过期则返回 None
        """
        cache_key = self._get_cache_key(messages, **kwargs)
        cache_file = self._get_cache_file(cache_key)

        if not self._is_cache_valid(cache_file):
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                return cache_data.get("result")
        except Exception:
            # 缓存文件损坏，返回 None
            return None

    def set(self, messages: list, result: Any, **kwargs) -> None:
        """
        设置缓存

        Args:
            messages: 消息列表
            result: 要缓存的结果
            **kwargs: 其他参数
        """
        cache_key = self._get_cache_key(messages, **kwargs)
        cache_file = self._get_cache_file(cache_key)

        cache_data = {
            "cache_key": cache_key,
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "metadata": kwargs,
        }

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception:
            logger.exception(f"Cache write failed for {cache_file}")

    def clear(self) -> None:
        """清空所有缓存"""
        if os.path.exists(self.cache_dir):
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".json"):
                    cache_file = os.path.join(self.cache_dir, filename)
                    try:
                        os.remove(cache_file)
                    except Exception:
                        logger.exception(f"Failed to remove cache file {cache_file}")

    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        if not os.path.exists(self.cache_dir):
            return {
                "total_files": 0,
                "valid_files": 0,
                "expired_files": 0,
                "total_size": 0,
            }

        valid_files = 0
        expired_files = 0
        total_size = 0

        for filename in os.listdir(self.cache_dir):
            if filename.endswith(".json"):
                cache_file = os.path.join(self.cache_dir, filename)
                total_size += os.path.getsize(cache_file)

                if self._is_cache_valid(cache_file):
                    valid_files += 1
                else:
                    expired_files += 1

        return {
            "total_files": valid_files + expired_files,
            "valid_files": valid_files,
            "expired_files": expired_files,
            "total_size": total_size,
            "cache_dir": self.cache_dir,
            "ttl_hours": self.ttl_hours,
        }


# 全局缓存实例
_global_cache = None


def get_cache() -> CacheManager:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheManager()
    return _global_cache


def clear_cache() -> None:
    """清空全局缓存"""
    global _global_cache
    if _global_cache:
        _global_cache.clear()


# 使用示例
if __name__ == "__main__":
    cache = CacheManager()

    # 测试缓存
    messages = [{"role": "user", "content": "测试消息"}]

    # 第一次获取（应该为空）
    result = cache.get(messages)
    print(f"第一次获取: {result}")

    # 设置缓存
    cache.set(messages, {"answer": "这是缓存的结果"})
    print("✓ 设置缓存成功")

    # 第二次获取（应该有值）
    result = cache.get(messages)
    print(f"第二次获取: {result}")

    # 查看统计
    stats = cache.get_stats()
    print(f"\n缓存统计: {stats}")
