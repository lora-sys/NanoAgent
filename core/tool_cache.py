"""Tool Result Cache — 减少 context token 开销"""

from collections import OrderedDict
from typing import Any, Dict, Optional

from config import get_config


class ToolResultCache:
    """
    LRU 缓存：存储工具完整结果，用摘要替代原文传给 LLM。

    原则（per Claude cookbook）：保留"调用发生过"的记录，丢弃原文。
    """

    def __init__(self, max_size: int = 50):
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_size = max_size
        self._next_id = 0

    def store(self, result: Dict[str, Any]) -> str:
        """存入缓存，返回 cache_key。"""
        key = f"tc_{self._next_id}"
        self._next_id += 1
        self._cache[key] = result
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)  # 淘汰最旧
        return key

    def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """取出完整结果并刷新 LRU 顺序。"""
        val = self._cache.get(key)
        if val is not None:
            self._cache.move_to_end(key)
        return val

    def summarize(self, tool_name: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """将完整结果转换为摘要，不含 matches/content 等大字段。"""
        if result.get("status") == "error" or (
            result.get("error")
            and not any(k in result for k in ("output", "exit_code", "cache_ref"))
        ):
            summary = {
                "tool": tool_name,
                "status": "error",
                "error": result.get("error"),
            }
            if "output" in result:
                summary["output"] = result["output"]
            if "exit_code" in result:
                summary["exit_code"] = result["exit_code"]
            return summary

        summary: Dict[str, Any] = {"tool": tool_name, "status": "ok"}

        if tool_name == "grep":
            stats = result.get("stats", {})
            summary["message"] = (
                f"{stats.get('total_matches', 0)} matches "
                f"in {stats.get('files_with_matches', 0)} files"
            )
            # 只保留 stats，不保留 matches 列表
            summary["stats"] = stats
            summary["cache_ref"] = self.store(result)

        elif tool_name == "read_file":
            content = result.get("content", "")
            lines = content.count("\n") + 1
            size = len(content)
            # 包含前 200 字符，避免模型幻觉（只看元数据会编造内容）
            preview = content[:200] + ("..." if len(content) > 200 else "")
            summary["message"] = f"文件共 {lines} 行，{size} 字符。前 200 字符: {preview}"
            summary["path"] = result.get("file_path", result.get("path", ""))
            summary["content_preview"] = preview
            # 内容缓存，外置
            summary["cache_ref"] = self.store(result)

        elif tool_name == "list_files":
            files = result.get("files", [])
            count = len(files) if isinstance(files, list) else 0
            summary["message"] = f"目录包含 {count} 个项目"
            summary["cache_ref"] = self.store(result)

        elif tool_name == "edit_file":
            summary["message"] = f"编辑完成: {result.get('action', 'unknown')}"
            summary["path"] = result.get("path", "")
            summary["cache_ref"] = self.store(result)

        elif tool_name == "run_bash":
            output = result.get("output", "")[:500]  # 截断 output
            exit_code = result.get("exit_code", -1)
            summary["message"] = f"exit={exit_code}, output_len={len(output)}"
            summary["output"] = output
            summary["cache_ref"] = self.store(result)

        elif tool_name == "plan":
            summary["message"] = "计划生成完成"
            summary["cache_ref"] = self.store(result)

        else:
            # 通用策略：只保留前 3 个键
            items = list(result.items())[:3]
            summary["message"] = ", ".join(f"{k}={v}" for k, v in items)
            summary["cache_ref"] = self.store(result)

        return summary

    def clear(self):
        self._cache.clear()

    @property
    def size(self) -> int:
        return len(self._cache)


# 全局单例
_cache: Optional[ToolResultCache] = None


def get_tool_cache() -> ToolResultCache:
    global _cache
    if _cache is None:
        cfg = get_config()
        cache_cfg = cfg.get("tool_result", {})
        max_size = cache_cfg.get("cache_size", 50)
        _cache = ToolResultCache(max_size=max_size)
    return _cache


def reset_tool_cache(cache: Optional[ToolResultCache] = None) -> None:
    """重置全局 cache，支持替换实例或清空后重建。"""
    global _cache
    _cache = cache
