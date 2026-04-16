"""评估系统 - 基于 Anthropic 最佳实践的代理评估框架

遵循 Anthropic 的工具评估原则：
- 基于真实世界场景的评估任务
- 多步骤工具调用的复杂任务
- 可验证的结果和指标收集
- 透明的推理过程和错误分析
- 性能优化和语义验证
"""

import time
from typing import Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum

from core.performance_optimizer import ToolCallOptimizer, ToolResponseCompressor
from core.semantic_verifier import SemanticVerifier, SemanticMatchType


class TaskDifficulty(Enum):
    """任务难度级别"""

    BASIC = "basic"  # 基础任务：1-2次工具调用
    INTERMEDIATE = "intermediate"  # 中等任务：3-5次工具调用
    ADVANCED = "advanced"  # 高级任务：6-10次工具调用
    EXPERT = "expert"  # 专家任务：10+次工具调用


class VerificationType(Enum):
    """验证类型"""

    EXACT_MATCH = "exact_match"  # 精确匹配
    CONTAINS = "contains"  # 包含匹配
    TOOL_CALLS = "tool_calls"  # 工具调用验证
    CUSTOM = "custom"  # 自定义验证
    SEMANTIC = "semantic"  # 语义验证


@dataclass
class EvaluationMetrics:
    """评估指标"""

    task_name: str
    start_time: float
    end_time: float
    total_time: float
    tool_call_count: int
    token_consumption: int
    tool_errors: List[str]
    success: bool
    iterations: int
    tools_used: List[str]
    reasoning_steps: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_name": self.task_name,
            "total_time": self.total_time,
            "tool_call_count": self.tool_call_count,
            "token_consumption": self.token_consumption,
            "tool_errors": self.tool_errors,
            "success": self.success,
            "iterations": self.iterations,
            "tools_used": self.tools_used,
            "reasoning_steps": self.reasoning_steps,
        }


@dataclass
class EvaluationTask:
    """评估任务定义"""

    name: str
    description: str
    prompt: str
    difficulty: TaskDifficulty
    verification_type: VerificationType
    expected_result: Any
    expected_tools: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "description": self.description,
            "prompt": self.prompt,
            "difficulty": self.difficulty.value,
            "verification_type": self.verification_type.value,
            "expected_result": self.expected_result,
            "expected_tools": self.expected_tools,
            "context": self.context,
            "metadata": self.metadata,
        }


class Verifier:
    """结果验证器"""

    @staticmethod
    def verify(task: EvaluationTask, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证任务结果"""
        verification_result = {
            "task_name": task.name,
            "verification_type": task.verification_type.value,
            "passed": False,
            "details": {},
            "expected": task.expected_result,
            "actual": result,
        }

        try:
            # 提取响应文本
            response_text = Verifier._extract_response_text(result)
            verification_result["details"]["extracted_response_length"] = len(
                response_text
            )
            verification_result["details"]["response_preview"] = (
                response_text[:100] if response_text else "EMPTY"
            )

            if task.verification_type == VerificationType.EXACT_MATCH:
                verification_result["passed"] = Verifier._exact_match(
                    task.expected_result, response_text
                )

            elif task.verification_type == VerificationType.CONTAINS:
                verification_result["passed"] = Verifier._contains_match(
                    task.expected_result, response_text
                )

            elif task.verification_type == VerificationType.TOOL_CALLS:
                verification_result["passed"] = Verifier._tool_calls_match(
                    task.expected_tools, result.get("tools_used", [])
                )

            elif task.verification_type == VerificationType.CUSTOM:
                verification_result["passed"] = Verifier._custom_verify(task, result)

            elif task.verification_type == VerificationType.SEMANTIC:
                verification_result["passed"] = Verifier._semantic_verify(
                    task, response_text
                )

            # 添加验证详情
            verification_result["details"]["tools_used"] = result.get("tools_used", [])
            verification_result["details"]["status"] = result.get("status", "unknown")

        except Exception as e:
            import traceback

            verification_result["error"] = str(e)
            verification_result["traceback"] = traceback.format_exc()
            verification_result["passed"] = False

        return verification_result

    @staticmethod
    def _extract_response_text(result: Dict[str, Any]) -> str:
        """从结果中提取响应文本"""
        # 首先尝试直接从结果中提取
        if "response" in result:
            return result["response"]

        # 尝试从 result 中提取最后的 assistant 响应
        # Agent 的结果可能包含 conversation 字段
        if "conversation" in result:
            conversation = result["conversation"]
            for msg in reversed(conversation):
                if msg.get("role") == "assistant":
                    content = msg.get("content", "")
                    # 提取 <response> 标签内容
                    import re

                    response_match = re.search(
                        r"<response>(.*?)</response>", content, re.DOTALL
                    )
                    if response_match:
                        return response_match.group(1).strip()
                    # 如果没有 response 标签，返回整个内容
                    return content

        # 检查是否有 spec 文件，尝试读取
        if "spec_file" in result and result["spec_file"]:
            try:
                from pathlib import Path

                spec_path = Path(result["spec_file"])
                if spec_path.exists():
                    import json

                    with open(spec_path, "r", encoding="utf-8") as f:
                        spec_data = json.load(f)
                        # 从 spec 中提取最后的 assistant 响应
                        conversation = spec_data.get("conversation", [])
                        for msg in reversed(conversation):
                            if msg.get("role") == "assistant":
                                content = msg.get("content", "")
                                # 提取 <response> 标签内容
                                import re

                                response_match = re.search(
                                    r"<response>(.*?)</response>", content, re.DOTALL
                                )
                                if response_match:
                                    return response_match.group(1).strip()
                                return content
            except Exception:
                # 如果读取失败，继续尝试其他方法
                pass

        # 如果所有方法都失败，返回空字符串
        return ""

    @staticmethod
    def _exact_match(expected: Any, actual: Dict[str, Any]) -> bool:
        """精确匹配验证"""
        response_text = actual.get("response", "")
        if isinstance(expected, str):
            return expected.strip() == response_text.strip()
        return str(expected) == response_text

    @staticmethod
    def _contains_match(expected: Any, response_text: str) -> bool:
        """包含匹配验证"""
        if isinstance(expected, str):
            return expected.lower() in response_text.lower()
        if isinstance(expected, list):
            return all(item.lower() in response_text.lower() for item in expected)
        return str(expected).lower() in response_text.lower()

    @staticmethod
    def _tool_calls_match(expected: List[str], actual: List[str]) -> bool:
        """工具调用验证"""
        if not expected:
            return True  # 没有预期工具，任何工具调用都算通过

        # 检查是否所有预期工具都被使用
        expected_set = set(expected)
        actual_set = set(actual)

        # 至少包含所有预期工具
        return expected_set.issubset(actual_set)

    @staticmethod
    def _custom_verify(task: EvaluationTask, result: Dict[str, Any]) -> bool:
        """自定义验证"""
        # 可以在任务定义中添加自定义验证逻辑
        custom_verifier = task.metadata.get("custom_verifier")
        if custom_verifier and callable(custom_verifier):
            return custom_verifier(task, result)
        return False

    @staticmethod
    def _semantic_verify(task: EvaluationTask, result: str) -> bool:
        """语义验证（使用精确的语义验证器）"""
        verifier = SemanticVerifier()

        # 使用语义相似度验证
        semantic_result = verifier.verify_semantic_match(
            expected=task.expected_result,
            actual=result,
            match_type=SemanticMatchType.SEMANTIC_SIMILAR,
        )

        # 返回是否匹配（置信度阈值0.7）
        return semantic_result.is_match(threshold=0.7)


class EvaluationRunner:
    """评估运行器"""

    def __init__(self, agent):
        """初始化评估运行器"""
        self.agent = agent
        self.results: List[Dict[str, Any]] = []
        self.metrics: List[EvaluationMetrics] = []
        self.performance_optimizer = ToolCallOptimizer()
        self.response_compressor = ToolResponseCompressor()

    def run_task(
        self, task: EvaluationTask, force_traditional_mode: bool = True
    ) -> Dict[str, Any]:
        """运行单个评估任务

        Args:
            task: 评估任务
            force_traditional_mode: 强制使用传统模式（避免自动选择提示链模式）
        """
        print(f"\n🎯 运行评估任务: {task.name}")
        print(f"📋 描述: {task.description}")
        print(f"📊 难度: {task.difficulty.value}")
        print(f"🔧 预期工具: {task.expected_tools}")
        print("-" * 80)

        start_time = time.time()
        tool_errors = []

        try:
            # 临时禁用提示链模式的自动选择
            if force_traditional_mode and hasattr(self.agent, "_should_use_chain"):
                original_method = self.agent._should_use_chain
                self.agent._should_use_chain = lambda task: False

            # 运行任务
            result = self.agent.run(task.prompt, max_iterations=20)

            # 恢复原始方法
            if force_traditional_mode and hasattr(self.agent, "_should_use_chain"):
                self.agent._should_use_chain = original_method

            # 收集指标
            metrics = EvaluationMetrics(
                task_name=task.name,
                start_time=start_time,
                end_time=time.time(),
                total_time=time.time() - start_time,
                tool_call_count=len(result.get("tools_used", [])),
                token_consumption=0,  # 需要从 LLM 客户端获取
                tool_errors=tool_errors,
                success=result.get("status") == "completed",
                iterations=result.get("iterations", 0),
                tools_used=result.get("tools_used", []),
                reasoning_steps=[],  # 需要从对话历史中提取
            )

            # 验证结果
            verification = Verifier.verify(task, result)

            # 组合结果
            task_result = {
                "task": task.to_dict(),
                "metrics": metrics.to_dict(),
                "verification": verification,
                "result": result,
            }

            # 输出结果
            print(f"✅ 状态: {result.get('status', 'unknown')}")
            print(f"🔧 使用的工具: {result.get('tools_used', [])}")
            print(f"🔄 迭代次数: {result.get('iterations', 0)}")
            print(f"⏱️ 执行时间: {metrics.total_time:.2f}秒")
            print(f"✅ 验证结果: {'通过' if verification['passed'] else '失败'}")

            if not verification["passed"]:
                print(f"❌ 验证详情: {verification.get('details', 'N/A')}")

            # 记录性能数据到优化器
            for tool_name in result.get("tools_used", []):
                self.performance_optimizer.record_tool_call(
                    tool_name=tool_name,
                    execution_time=metrics.total_time
                    / len(result.get("tools_used", [1])),
                    success=(result.get("status") == "completed"),
                    expected=(tool_name in task.expected_tools),
                    token_cost=0,  # 可以从 LLM 客户端获取
                )

            self.results.append(task_result)
            self.metrics.append(metrics)

            return task_result

        except Exception as e:
            print(f"❌ 任务执行失败: {e}")
            error_result = {"task": task.to_dict(), "error": str(e), "success": False}
            self.results.append(error_result)
            return error_result

    def run_evaluation_suite(self, tasks: List[EvaluationTask]) -> Dict[str, Any]:
        """运行评估套件"""
        print("🚀 开始运行评估套件")
        print(f"📊 总任务数: {len(tasks)}")
        print("=" * 80)

        suite_start_time = time.time()

        for task in tasks:
            self.run_task(task)
            print()

        total_time = time.time() - suite_start_time

        # 生成汇总报告
        summary = self._generate_summary(total_time)

        print("=" * 80)
        print("📊 评估套件完成")
        print(summary)

        # 添加性能优化建议
        print("\n🚀 性能优化建议")
        print("=" * 80)
        optimization_suggestions = self.performance_optimizer.analyze_performance()

        if optimization_suggestions:
            for i, suggestion in enumerate(optimization_suggestions, 1):
                print(
                    f"\n{i}. {suggestion.tool_name} - {suggestion.issue_type.upper()} ({suggestion.severity})"
                )
                print(f"   问题: {suggestion.description}")
                print(f"   建议: {suggestion.suggestion}")
                print(f"   预期改进: {suggestion.expected_improvement}")
        else:
            print("✅ 没有发现明显的性能问题")

        # 添加性能报告
        performance_report = self.performance_optimizer.get_performance_report()
        print("\n📊 性能报告摘要:")
        print(f"   总调用次数: {performance_report['summary']['total_calls']}")
        print(f"   成功率: {performance_report['summary']['overall_success_rate']:.1%}")
        print(f"   分析工具数: {performance_report['summary']['tools_analyzed']}")

        return {
            "tasks": self.results,
            "summary": summary,
            "total_time": total_time,
            "performance_report": performance_report,
            "optimization_suggestions": [
                {
                    "tool": s.tool_name,
                    "issue": s.issue_type,
                    "severity": s.severity,
                    "suggestion": s.suggestion,
                    "expected_improvement": s.expected_improvement,
                }
                for s in optimization_suggestions
            ],
        }

    def _generate_summary(self, total_time: float) -> Dict[str, Any]:
        """生成汇总报告"""
        total_tasks = len(self.results)
        successful_tasks = sum(
            1 for r in self.results if r.get("verification", {}).get("passed", False)
        )

        # 按难度统计
        difficulty_stats = {}
        for result in self.results:
            difficulty = result["task"]["difficulty"]
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = {"total": 0, "passed": 0}
            difficulty_stats[difficulty]["total"] += 1
            if result.get("verification", {}).get("passed", False):
                difficulty_stats[difficulty]["passed"] += 1

        # 工具使用统计
        tool_usage = {}
        for result in self.results:
            for tool in result.get("result", {}).get("tools_used", []):
                if tool not in tool_usage:
                    tool_usage[tool] = 0
                tool_usage[tool] += 1

        # 错误统计
        all_errors = []
        for result in self.results:
            if "error" in result:
                all_errors.append(result["error"])
            for error in result.get("metrics", {}).get("tool_errors", []):
                all_errors.append(error)

        summary = {
            "total_tasks": total_tasks,
            "successful_tasks": successful_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "total_time": total_time,
            "average_time_per_task": total_time / total_tasks if total_tasks > 0 else 0,
            "difficulty_stats": difficulty_stats,
            "tool_usage": tool_usage,
            "common_errors": all_errors,
        }

        return summary


class EvaluationAnalyzer:
    """评估结果分析器"""

    @staticmethod
    def analyze_results(evaluation_results: Dict[str, Any]) -> Dict[str, Any]:
        """分析评估结果"""
        results = evaluation_results["tasks"]
        summary = evaluation_results["summary"]

        analysis = {
            "performance_analysis": EvaluationAnalyzer._analyze_performance(results),
            "tool_usage_analysis": EvaluationAnalyzer._analyze_tool_usage(results),
            "error_analysis": EvaluationAnalyzer._analyze_errors(results),
            "improvement_suggestions": EvaluationAnalyzer._generate_suggestions(
                results, summary
            ),
        }

        return analysis

    @staticmethod
    def _analyze_performance(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """性能分析"""
        performance_data = []

        for result in results:
            if "metrics" in result:
                metrics = result["metrics"]
                performance_data.append(
                    {
                        "task": result["task"]["name"],
                        "time": metrics["total_time"],
                        "iterations": metrics["iterations"],
                        "tool_calls": metrics["tool_call_count"],
                        "success": result["verification"]["passed"],
                    }
                )

        # 计算统计信息
        if performance_data:
            avg_time = sum(p["time"] for p in performance_data) / len(performance_data)
            avg_iterations = sum(p["iterations"] for p in performance_data) / len(
                performance_data
            )
            avg_tool_calls = sum(p["tool_calls"] for p in performance_data) / len(
                performance_data
            )
        else:
            avg_time = avg_iterations = avg_tool_calls = 0

        return {
            "average_execution_time": avg_time,
            "average_iterations": avg_iterations,
            "average_tool_calls": avg_tool_calls,
            "performance_details": performance_data,
        }

    @staticmethod
    def _analyze_tool_usage(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """工具使用分析"""
        tool_stats = {}
        unused_tools = set()

        for result in results:
            task = result["task"]
            expected_tools = task.get("expected_tools", [])
            actual_tools = result.get("result", {}).get("tools_used", [])

            # 统计实际使用的工具
            for tool in actual_tools:
                if tool not in tool_stats:
                    tool_stats[tool] = {"used": 0, "expected": 0, "unexpected": 0}
                tool_stats[tool]["used"] += 1

                # 检查是否在预期工具中
                if tool in expected_tools:
                    tool_stats[tool]["expected"] += 1
                else:
                    tool_stats[tool]["unexpected"] += 1

            # 记录未使用的预期工具
            for tool in expected_tools:
                if tool not in actual_tools:
                    unused_tools.add((task["name"], tool))

        return {
            "tool_statistics": tool_stats,
            "unused_expected_tools": list(unused_tools),
            "recommendations": EvaluationAnalyzer._generate_tool_recommendations(
                tool_stats
            ),
        }

    @staticmethod
    def _analyze_errors(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """错误分析"""
        errors = []
        failed_tasks = []

        for result in results:
            if not result.get("verification", {}).get("passed", False):
                failed_tasks.append(result["task"]["name"])

            if "error" in result:
                errors.append(
                    {"task": result["task"]["name"], "error": result["error"]}
                )

            tool_errors = result.get("metrics", {}).get("tool_errors", [])
            if tool_errors:
                for error in tool_errors:
                    errors.append({"task": result["task"]["name"], "error": error})

        return {
            "failed_tasks": failed_tasks,
            "error_list": errors,
            "error_frequency": EvaluationAnalyzer._count_error_frequency(errors),
        }

    @staticmethod
    def _count_error_frequency(errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计错误频率"""
        frequency = {}
        for error in errors:
            error_msg = error["error"]
            frequency[error_msg] = frequency.get(error_msg, 0) + 1
        return frequency

    @staticmethod
    def _generate_tool_recommendations(tool_stats: Dict[str, Any]) -> List[str]:
        """生成工具改进建议"""
        recommendations = []

        for tool, stats in tool_stats.items():
            # 检查意外使用频率
            if stats["unexpected"] > stats["expected"]:
                recommendations.append(
                    f"工具 '{tool}' 被意外使用 {stats['unexpected']} 次，"
                    f"可能需要改进描述或添加更多使用示例"
                )

            # 检查使用频率
            if stats["used"] == 0:
                recommendations.append(
                    f"工具 '{tool}' 从未被使用，考虑是否需要保留或改进其描述"
                )

        return recommendations

    @staticmethod
    def _generate_suggestions(
        results: List[Dict[str, Any]], summary: Dict[str, Any]
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []

        success_rate = summary.get("success_rate", 0)

        if success_rate < 0.5:
            suggestions.append("成功率较低，建议检查系统提示和工具描述")
        elif success_rate < 0.8:
            suggestions.append("成功率中等，建议优化工具调用逻辑和错误处理")
        else:
            suggestions.append("成功率良好，可以考虑增加更复杂的评估任务")

        # 基于难度分析的建议
        difficulty_stats = summary.get("difficulty_stats", {})
        for difficulty, stats in difficulty_stats.items():
            pass_rate = stats["passed"] / stats["total"] if stats["total"] > 0 else 0
            if pass_rate < 0.5:
                suggestions.append(
                    f"{difficulty} 难度任务通过率较低 ({pass_rate:.1%})，"
                    f"建议针对该难度级别优化"
                )

        return suggestions


def create_evaluation_runner(agent):
    """创建评估运行器的便捷函数"""
    return EvaluationRunner(agent)
