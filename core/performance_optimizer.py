"""性能优化器 - 简化版本

遵循 AGENT.md 原则：
- clean + zero magic
- more use builtin function
- keep it code readable and clean
"""

from typing import Dict, List, Any
from collections import defaultdict


class PerformanceOptimizer:
    """简化的性能优化器"""

    def __init__(self):
        self.tool_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "calls": 0,
                "success": 0,
                "failures": 0,
                "total_time": 0.0,
                "unnecessary": 0,
            }
        )

    def record_call(
        self, tool_name: str, execution_time: float, success: bool, expected: bool
    ) -> None:
        """记录工具调用"""
        stats = self.tool_stats[tool_name]
        stats["calls"] += 1
        stats["total_time"] += execution_time

        if success:
            stats["success"] += 1
            if not expected:
                stats["unnecessary"] += 1
        else:
            stats["failures"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        result = {}
        for tool_name, stats in self.tool_stats.items():
            if stats["calls"] > 0:
                result[tool_name] = {
                    "calls": stats["calls"],
                    "success_rate": stats["success"] / stats["calls"],
                    "avg_time": stats["total_time"] / stats["calls"],
                    "unnecessary_rate": stats["unnecessary"] / stats["calls"],
                }
        return result

    def get_suggestions(self) -> List[str]:
        """获取优化建议"""
        suggestions = []

        for tool_name, stats in self.get_stats().items():
            # 检查不必要的调用
            if stats["unnecessary_rate"] > 0.3:
                suggestions.append(
                    f"{tool_name}: {stats['unnecessary_rate']:.0%} 的调用不必要，"
                    f"改进工具描述"
                )

            # 检查响应时间
            if stats["avg_time"] > 5.0:
                suggestions.append(
                    f"{tool_name}: 平均响应 {stats['avg_time']:.1f}s，考虑优化或缓存"
                )

            # 检查成功率
            if stats["success_rate"] < 0.8:
                suggestions.append(
                    f"{tool_name}: 成功率仅 {stats['success_rate']:.0%}，检查错误处理"
                )

        return suggestions


class ResponseCompressor:
    """简化的响应压缩器"""

    @staticmethod
    def compress_file_list(files: List[Dict[str, str]]) -> Dict[str, Any]:
        """压缩文件列表"""
        file_names = [f["filename"] for f in files if f["type"] == "file"]
        dir_names = [f["filename"] for f in files if f["type"] == "dir"]

        return {
            "files": file_names[:20],
            "dirs": dir_names[:10],
            "total_files": len(file_names),
            "total_dirs": len(dir_names),
        }

    @staticmethod
    def compress_content(content: str, max_len: int = 2000) -> str:
        """压缩内容"""
        if len(content) <= max_len:
            return content

        # 在换行处截断
        truncated = content[:max_len]
        last_newline = truncated.rfind("\n")
        if last_newline > max_len * 0.8:
            truncated = truncated[:last_newline]

        return truncated + f"\n... [剩余 {len(content) - len(truncated)} 字符]"


def create_optimizer() -> PerformanceOptimizer:
    """创建优化器"""
    return PerformanceOptimizer()


def create_compressor() -> ResponseCompressor:
    """创建压缩器"""
    return ResponseCompressor()
