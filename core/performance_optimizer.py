"""性能优化器 - 基于评估结果优化工具调用

遵循 AGENT.md 原则：
- 优化工具响应的 token 效率
- 减少不必要的工具调用
- 提高工具调用的准确性
"""

import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ToolPerformanceMetrics:
    """工具性能指标"""

    tool_name: str
    call_count: int
    success_count: int
    failure_count: int
    avg_execution_time: float
    avg_token_cost: int
    unnecessary_calls: int
    efficient_calls: int

    def get_efficiency_score(self) -> float:
        """计算效率分数 (0-1)"""
        if self.call_count == 0:
            return 1.0

        success_rate = self.success_count / self.call_count
        efficiency_rate = (
            self.efficient_calls / self.call_count if self.call_count > 0 else 1.0
        )

        # 综合效率分数：成功率和效率率的加权平均
        return success_rate * 0.6 + efficiency_rate * 0.4


@dataclass
class OptimizationSuggestion:
    """优化建议"""

    tool_name: str
    issue_type: (
        str  # "unnecessary_calls", "slow_response", "high_token_cost", "inaccurate"
    )
    severity: str  # "low", "medium", "high"
    description: str
    suggestion: str
    expected_improvement: str


class ToolCallOptimizer:
    """工具调用优化器"""

    def __init__(self):
        """初始化优化器"""
        self.tool_metrics: Dict[str, ToolPerformanceMetrics] = {}
        self.optimization_history: List[Dict[str, Any]] = []
        self.pattern_cache: Dict[str, str] = {}  # 缓存任务模式到最佳工具的映射

    def record_tool_call(
        self,
        tool_name: str,
        execution_time: float,
        success: bool,
        expected: bool = True,
        token_cost: int = 0,
    ) -> None:
        """记录工具调用数据"""
        if tool_name not in self.tool_metrics:
            self.tool_metrics[tool_name] = ToolPerformanceMetrics(
                tool_name=tool_name,
                call_count=0,
                success_count=0,
                failure_count=0,
                avg_execution_time=0.0,
                avg_token_cost=0,
                unnecessary_calls=0,
                efficient_calls=0,
            )

        metrics = self.tool_metrics[tool_name]
        metrics.call_count += 1

        if success:
            metrics.success_count += 1
            if expected:
                metrics.efficient_calls += 1
            else:
                metrics.unnecessary_calls += 1
        else:
            metrics.failure_count += 1

        # 更新平均执行时间
        metrics.avg_execution_time = (
            metrics.avg_execution_time * (metrics.call_count - 1) + execution_time
        ) / metrics.call_count

        # 更新平均 token 成本
        metrics.avg_token_cost = (
            metrics.avg_token_cost * (metrics.call_count - 1) + token_cost
        ) / metrics.call_count

    def analyze_performance(self) -> List[OptimizationSuggestion]:
        """分析性能并生成优化建议"""
        suggestions = []

        for tool_name, metrics in self.tool_metrics.items():
            # 检查不必要的调用
            unnecessary_rate = (
                metrics.unnecessary_calls / metrics.call_count
                if metrics.call_count > 0
                else 0
            )
            if unnecessary_rate > 0.3:  # 超过30%的调用是不必要的
                suggestions.append(
                    OptimizationSuggestion(
                        tool_name=tool_name,
                        issue_type="unnecessary_calls",
                        severity="high" if unnecessary_rate > 0.5 else "medium",
                        description=f"工具 {tool_name} 有 {unnecessary_rate:.1%} 的调用是不必要的",
                        suggestion="改进工具描述和系统提示，让模型更准确地判断何时使用该工具",
                        expected_improvement=f"可减少 {unnecessary_rate:.1%} 的不必要调用",
                    )
                )

            # 检查响应时间
            if metrics.avg_execution_time > 5.0:  # 超过5秒
                suggestions.append(
                    OptimizationSuggestion(
                        tool_name=tool_name,
                        issue_type="slow_response",
                        severity="medium",
                        description=f"工具 {tool_name} 平均响应时间较长 ({metrics.avg_execution_time:.2f}秒)",
                        suggestion="优化工具实现，考虑缓存结果或异步处理",
                        expected_improvement="可减少 30-50% 的响应时间",
                    )
                )

            # 检查 token 成本
            if metrics.avg_token_cost > 1000:  # 超过1000 tokens
                suggestions.append(
                    OptimizationSuggestion(
                        tool_name=tool_name,
                        issue_type="high_token_cost",
                        severity="medium",
                        description=f"工具 {tool_name} 平均 token 消耗较高 ({metrics.avg_token_cost} tokens)",
                        suggestion="优化工具响应格式，减少冗余信息，使用更简洁的数据结构",
                        expected_improvement="可减少 40-60% 的 token 消耗",
                    )
                )

            # 检查成功率
            success_rate = (
                metrics.success_count / metrics.call_count
                if metrics.call_count > 0
                else 0
            )
            if success_rate < 0.8:  # 成功率低于80%
                suggestions.append(
                    OptimizationSuggestion(
                        tool_name=tool_name,
                        issue_type="inaccurate",
                        severity="high",
                        description=f"工具 {tool_name} 成功率较低 ({success_rate:.1%})",
                        suggestion="检查工具实现，改进错误处理，添加参数验证",
                        expected_improvement="可提升至 90%+ 的成功率",
                    )
                )

        # 按严重程度排序
        severity_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda x: severity_order.get(x.severity, 3))

        return suggestions

    def optimize_tool_response(self, tool_name: str, response: Any) -> Any:
        """优化工具响应以减少 token 消耗"""
        if isinstance(response, dict):
            return self._optimize_dict_response(tool_name, response)
        elif isinstance(response, str):
            return self._optimize_string_response(tool_name, response)
        elif isinstance(response, list):
            return self._optimize_list_response(tool_name, response)
        else:
            return response

    def _optimize_dict_response(
        self, tool_name: str, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """优化字典响应"""
        optimized = {}

        for key, value in response.items():
            # 移除冗余字段
            if key in ["debug_info", "metadata", "timestamp"]:
                continue

            # 优化字段名
            if key == "file_path":
                optimized["path"] = value
            elif key == "directory":
                optimized["path"] = value
            else:
                optimized[key] = value

            # 递归优化嵌套结构
            if isinstance(value, dict):
                optimized[key] = self._optimize_dict_response(tool_name, value)
            elif isinstance(value, list):
                optimized[key] = self._optimize_list_response(tool_name, value)

        return optimized

    def _optimize_string_response(self, tool_name: str, response: str) -> str:
        """优化字符串响应"""
        # 移除多余的空白字符
        optimized = " ".join(response.split())

        # 如果是文件内容，只返回前 2000 个字符
        if tool_name == "read_file" and len(optimized) > 2000:
            optimized = optimized[:2000] + "... [内容截断]"

        return optimized

    def _optimize_list_response(self, tool_name: str, response: List[Any]) -> List[Any]:
        """优化列表响应"""
        # 限制列表长度
        if len(response) > 50:
            response = response[:50]

        optimized = []
        for item in response:
            if isinstance(item, dict):
                optimized.append(self._optimize_dict_response(tool_name, item))
            elif isinstance(item, str):
                # 限制字符串长度
                if len(item) > 100:
                    item = item[:100] + "..."
                optimized.append(item)
            else:
                optimized.append(item)

        return optimized

    def learn_from_pattern(self, task_pattern: str, best_tool: str) -> None:
        """从任务模式中学习最佳工具选择"""
        self.pattern_cache[task_pattern] = best_tool

    def suggest_tool_for_task(self, task: str) -> Optional[str]:
        """基于任务模式建议最佳工具"""
        # 简单的关键词匹配
        task_lower = task.lower()

        if "读取" in task_lower or "read" in task_lower or "文件" in task_lower:
            return "read_file"
        elif "列出" in task_lower or "list" in task_lower or "目录" in task_lower:
            return "list_files"
        elif "运行" in task_lower or "run" in task_lower or "命令" in task_lower:
            return "run_bash"
        elif "编辑" in task_lower or "edit" in task_lower:
            return "edit_file"

        # 检查缓存
        for pattern, tool in self.pattern_cache.items():
            if pattern in task_lower:
                return tool

        return None

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        total_calls = sum(m.call_count for m in self.tool_metrics.values())
        total_success = sum(m.success_count for m in self.tool_metrics.values())

        return {
            "summary": {
                "total_calls": total_calls,
                "total_success": total_success,
                "overall_success_rate": total_success / total_calls
                if total_calls > 0
                else 0,
                "tools_analyzed": len(self.tool_metrics),
            },
            "tool_metrics": {
                name: {
                    "call_count": m.call_count,
                    "success_rate": m.success_count / m.call_count
                    if m.call_count > 0
                    else 0,
                    "avg_execution_time": m.avg_execution_time,
                    "efficiency_score": m.get_efficiency_score(),
                }
                for name, m in self.tool_metrics.items()
            },
            "optimization_suggestions": [
                {
                    "tool": s.tool_name,
                    "issue": s.issue_type,
                    "severity": s.severity,
                    "suggestion": s.suggestion,
                }
                for s in self.analyze_performance()
            ],
        }


class ToolResponseCompressor:
    """工具响应压缩器 - 优化 token 效率"""

    @staticmethod
    def compress_file_list(files: List[Dict[str, str]]) -> Dict[str, Any]:
        """压缩文件列表响应"""
        # 分离文件和目录
        files_only = [f["filename"] for f in files if f["type"] == "file"]
        dirs_only = [f["filename"] for f in files if f["type"] == "dir"]

        return {
            "files": files_only[:20],  # 最多返回20个文件
            "dirs": dirs_only[:10],  # 最多返回10个目录
            "total_files": len(files_only),
            "total_dirs": len(dirs_only),
        }

    @staticmethod
    def compress_file_content(content: str, max_length: int = 2000) -> str:
        """压缩文件内容响应"""
        if len(content) <= max_length:
            return content

        # 智能截断：在行边界处截断
        truncated = content[:max_length]
        last_newline = truncated.rfind("\n")

        if last_newline > max_length * 0.8:  # 如果最后一个换行符在合理位置
            truncated = truncated[:last_newline]

        return truncated + f"\n... [剩余 {len(content) - len(truncated)} 字符已截断]"

    @staticmethod
    def compress_command_output(output: str, max_lines: int = 50) -> str:
        """压缩命令输出响应"""
        lines = output.split("\n")

        if len(lines) <= max_lines:
            return output

        # 保留前25行和后25行
        kept_lines = lines[: max_lines // 2] + lines[-max_lines // 2 :]

        return (
            "\n".join(kept_lines) + f"\n... [共 {len(lines)} 行，已显示 {max_lines} 行]"
        )

    @staticmethod
    def estimate_token_savings(original: Any, compressed: Any) -> Dict[str, int]:
        """估算 token 节省"""
        original_str = json.dumps(original, ensure_ascii=False)
        compressed_str = json.dumps(compressed, ensure_ascii=False)

        # 粗略估算：4字符 ≈ 1 token
        original_tokens = len(original_str) // 4
        compressed_tokens = len(compressed_str) // 4

        return {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "saved_tokens": original_tokens - compressed_tokens,
            "savings_percentage": (
                (original_tokens - compressed_tokens) / original_tokens * 100
            )
            if original_tokens > 0
            else 0,
        }


def create_performance_optimizer() -> ToolCallOptimizer:
    """创建性能优化器的便捷函数"""
    return ToolCallOptimizer()


def create_response_compressor() -> ToolResponseCompressor:
    """创建响应压缩器的便捷函数"""
    return ToolResponseCompressor()
