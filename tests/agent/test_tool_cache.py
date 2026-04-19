"""tool_cache 单元测试"""

from core.tool_cache import ToolResultCache


class TestToolResultCache:
    """ToolResultCache 核心功能测试"""

    def test_store_and_retrieve(self):
        """存入并取出"""
        cache = ToolResultCache(max_size=3)
        result = {"foo": "bar"}
        key = cache.store(result)
        assert cache.retrieve(key) == result

    def test_lru_eviction(self):
        """超出容量时淘汰最旧"""
        cache = ToolResultCache(max_size=3)
        keys = [cache.store({"v": i}) for i in range(5)]
        assert keys[0] not in cache._cache  # 第一条被淘汰
        assert cache.size == 3

    def test_grep_summarize(self):
        """grep 工具：摘要只保留 stats，不保留 matches"""
        cache = ToolResultCache()
        result = {
            "matches": [{"file": "a.py", "line": 1, "content": "def foo()"}] * 100,
            "stats": {"total_matches": 100, "files_with_matches": 5},
            "path": "/src",
            "exit_code": 0,
        }
        summary = cache.summarize("grep", result)

        assert "matches" not in summary
        assert "cache_ref" in summary
        assert summary["stats"] == {"total_matches": 100, "files_with_matches": 5}
        assert "100 matches in 5 files" in summary["message"]

    def test_read_file_summarize(self):
        """read_file 工具：摘要不包含内容"""
        cache = ToolResultCache()
        result = {
            "file_path": "/src/main.py",
            "content": "line\n" * 200,
        }
        summary = cache.summarize("read_file", result)

        assert "content" not in summary
        assert "cache_ref" in summary
        assert summary["message"] == "文件共 201 行，1000 字符"

    def test_run_bash_summarize(self):
        """run_bash 工具：output 截断"""
        cache = ToolResultCache()
        result = {
            "output": "x" * 1000,
            "exit_code": 0,
        }
        summary = cache.summarize("run_bash", result)

        assert len(summary["output"]) <= 500
        assert "cache_ref" in summary
        assert summary["message"].startswith("exit=0")

    def test_error_summarize(self):
        """错误结果直接返回"""
        cache = ToolResultCache()
        result = {"error": "file not found"}
        summary = cache.summarize("read_file", result)

        assert summary["status"] == "error"
        assert summary["error"] == "file not found"
        assert "cache_ref" not in summary

    def test_unknown_tool_fallback(self):
        """未知工具走通用摘要"""
        cache = ToolResultCache()
        result = {"key1": "val1", "key2": "val2", "key3": "val3"}
        summary = cache.summarize("unknown_tool", result)

        assert "cache_ref" in summary
        assert summary["status"] == "ok"

    def test_clear(self):
        """清空缓存"""
        cache = ToolResultCache()
        cache.store({"a": 1})
        cache.store({"b": 2})
        assert cache.size == 2
        cache.clear()
        assert cache.size == 0
