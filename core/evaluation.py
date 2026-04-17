"""评估系统 - 简化版本

遵循 AGENT.md 原则：
- clean + zero magic
- more use builtin function
- keep it code readable and clean
"""

import time
import json
import re
from typing import Any, Dict, List
from dataclasses import dataclass, field
from enum import Enum

from core.performance_optimizer import create_optimizer, create_compressor
from core.semantic_verifier import create_verifier, MatchType


class Difficulty(Enum):
    """任务难度"""

    BASIC = "basic"  # 1-2次工具调用
    INTERMEDIATE = "intermediate"  # 3-5次工具调用
    ADVANCED = "advanced"  # 6-10次工具调用
    EXPERT = "expert"  # 10+次工具调用


class VerifyType(Enum):
    """验证类型"""

    EXACT = "exact"
    CONTAINS = "contains"
    TOOLS = "tools"
    TOOL_CALLS = "tool_calls"  # 别名
    SEMANTIC = "semantic"


# 别名 - 向后兼容
# 别名 - 向后兼容（必须在 Task 类定义之后定义）
TaskDifficulty = Difficulty
VerificationType = VerifyType
EvaluationTask = Task
EvaluationRunner = Runner
EvaluationAnalyzer = Evaluator


@dataclass
class Task:
    """评估任务"""

    name: str
    description: str
    prompt: str
    difficulty: Difficulty = Difficulty.BASIC
    verify_type: VerifyType = VerifyType.CONTAINS
    expected: Any = None
    expected_tools: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "prompt": self.prompt,
            "difficulty": self.difficulty.value,
            "verify_type": self.verify_type.value,
            "expected": self.expected,
            "expected_tools": self.expected_tools,
            "metadata": self.metadata,
        }


@dataclass
class Metrics:
    """评估指标"""

    task_name: str
    total_time: float
    tool_calls: int
    success: bool
    iterations: int
    tools_used: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_name": self.task_name,
            "total_time": self.total_time,
            "tool_calls": self.tool_calls,
            "success": self.success,
            "iterations": self.iterations,
            "tools_used": self.tools_used,
        }


class Evaluator:
    """评估器"""

    def __init__(self):
        self.verifier = create_verifier()
        self.optimizer = create_optimizer()
        self.compressor = create_compressor()

    def verify(self, task: Task, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证结果"""
        response_text = self._extract_response(result)

        if task.verify_type == VerifyType.EXACT:
            match_result = self.verifier.verify(
                task.expected, response_text, MatchType.EXACT
            )
        elif task.verify_type == VerifyType.CONTAINS:
            match_result = self.verifier.verify(
                task.expected, response_text, MatchType.CONTAINS
            )
        elif task.verify_type in (VerifyType.TOOLS, VerifyType.TOOL_CALLS):
            match_result = self.verifier.verify_tool_sequence(
                task.expected_tools, result.get("tools_used", [])
            )
        else:  # SEMANTIC
            match_result = self.verifier.verify(
                task.expected, response_text, MatchType.SEMANTIC
            )

        return {
            "task_name": task.name,
            "passed": match_result.matched,
            "confidence": match_result.confidence,
            "details": match_result.details,
            "tools_used": result.get("tools_used", []),
        }

    def _extract_response(self, result: Dict[str, Any]) -> str:
        """提取响应文本"""
        # 从 conversation 中提取最后的 assistant 响应
        if "conversation" in result:
            for msg in reversed(result["conversation"]):
                if msg.get("role") == "assistant":
                    content = msg.get("content", "")
                    # 提取 <response> 标签内容
                    match = re.search(r"<response>(.*?)</response>", content, re.DOTALL)
                    if match:
                        return match.group(1).strip()
                    return content

        # 尝试从 spec 文件读取
        if "spec_file" in result and result["spec_file"]:
            try:
                with open(result["spec_file"], "r", encoding="utf-8") as f:
                    spec_data = json.load(f)
                    for msg in reversed(spec_data.get("conversation", [])):
                        if msg.get("role") == "assistant":
                            content = msg.get("content", "")
                            match = re.search(
                                r"<response>(.*?)</response>", content, re.DOTALL
                            )
                            if match:
                                return match.group(1).strip()
                            return content
            except Exception:
                pass

        return ""

    def compress_response(self, tool_name: str, response: Any) -> Any:
        """压缩响应"""
        if tool_name == "list_files" and isinstance(response, dict):
            if "files" in response:
                return self.compressor.compress_file_list(response["files"])
        elif tool_name == "read_file" and isinstance(response, dict):
            if "content" in response:
                response["content"] = self.compressor.compress_content(
                    response["content"]
                )
        return response

    def analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """分析评估结果"""
        tasks = results.get("tasks", [])
        tool_usage = {}
        failed_tasks = []
        error_list = []

        for task_result in tasks:
            if not task_result.get("success", True):
                failed_tasks.append(task_result.get("task", {}).get("name", "unknown"))
            if "error" in task_result:
                error_list.append({
                    "task": task_result.get("task", {}).get("name", "unknown"),
                    "error": task_result.get("error", ""),
                })

        return {
            "performance_analysis": {
                "average_execution_time": 0,
                "average_iterations": 0,
                "average_tool_calls": 0,
            },
            "error_analysis": {
                "failed_tasks": failed_tasks,
                "error_list": error_list,
            },
            "improvement_suggestions": [],
        }


class Runner:
    """评估运行器"""

    def __init__(self, agent):
        self.agent = agent
        self.evaluator = Evaluator()
        self.results: List[Dict[str, Any]] = []

    def run_task(self, task: Task) -> Dict[str, Any]:
        """运行单个任务"""
        print(f"\n🎯 {task.name}")
        print(f"📋 {task.description}")

        start_time = time.time()

        try:
            # 运行任务
            result = self.agent.run(task.prompt, max_iterations=20)

            # 记录性能数据
            execution_time = time.time() - start_time
            for tool_name in result.get("tools_used", []):
                self.evaluator.optimizer.record_call(
                    tool_name,
                    execution_time / len(result.get("tools_used", [1])),
                    result.get("status") == "completed",
                    tool_name in task.expected_tools,
                )

            # 验证结果
            verification = self.evaluator.verify(task, result)

            # 创建指标
            metrics = Metrics(
                task_name=task.name,
                total_time=execution_time,
                tool_calls=len(result.get("tools_used", [])),
                success=result.get("status") == "completed",
                iterations=result.get("iterations", 0),
                tools_used=result.get("tools_used", []),
            )

            # 组合结果
            task_result = {
                "task": task.to_dict(),
                "metrics": metrics.to_dict(),
                "verification": verification,
                "result": result,
            }

            # 输出结果
            print(f"✅ 状态: {result.get('status')}")
            print(f"🔧 工具: {result.get('tools_used', [])}")
            print(f"⏱️ 时间: {execution_time:.2f}s")
            print(f"🎯 验证: {'通过' if verification['passed'] else '失败'}")

            self.results.append(task_result)
            return task_result

        except Exception as e:
            print(f"❌ 错误: {e}")
            error_result = {"task": task.to_dict(), "error": str(e), "success": False}
            self.results.append(error_result)
            return error_result

    def run_suite(self, tasks: List[Task]) -> Dict[str, Any]:
        """运行评估套件"""
        print("🚀 开始评估")
        print(f"📊 任务数: {len(tasks)}")
        print("=" * 80)

        start_time = time.time()

        for task in tasks:
            self.run_task(task)

        total_time = time.time() - start_time

        # 生成报告
        report = self._generate_report(total_time)

        print("\n" + "=" * 80)
        print("📊 评估完成")
        print(report)

        # 显示优化建议
        suggestions = self.evaluator.optimizer.get_suggestions()
        if suggestions:
            print("\n💡 优化建议:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"   {i}. {suggestion}")

        return {
            "tasks": self.results,
            "report": report,
            "summary": self._make_summary(report, total_time),
            "suggestions": suggestions,
            "total_time": total_time,
        }

    def run_evaluation_suite(self, tasks: List[Task]) -> Dict[str, Any]:
        """运行评估套件（向后兼容别名）"""
        return self.run_suite(tasks)

    def _make_summary(self, report: Dict[str, Any], total_time: float) -> Dict[str, Any]:
        """生成与 tests/run_evaluation.py 兼容的 summary"""
        difficulty_stats = {}
        for result in self.results:
            diff = result.get("task", {}).get("difficulty", "unknown")
            if diff not in difficulty_stats:
                difficulty_stats[diff] = {"total": 0, "passed": 0}
            difficulty_stats[diff]["total"] += 1
            if result.get("verification", {}).get("passed", False):
                difficulty_stats[diff]["passed"] += 1

        return {
            "total_tasks": report.get("total_tasks", 0),
            "successful_tasks": report.get("passed", 0),
            "success_rate": report.get("success_rate", 0),
            "total_time": total_time,
            "average_time_per_task": report.get("avg_time", 0),
            "difficulty_stats": difficulty_stats,
            "tool_usage": report.get("tool_usage", {}),
            "performance": report.get("performance", {}),
        }

    def _generate_report(self, total_time: float) -> Dict[str, Any]:
        """生成报告"""
        total = len(self.results)
        passed = sum(
            1 for r in self.results if r.get("verification", {}).get("passed", False)
        )

        # 工具使用统计
        tool_usage = {}
        for result in self.results:
            for tool in result.get("result", {}).get("tools_used", []):
                tool_usage[tool] = tool_usage.get(tool, 0) + 1

        # 性能统计
        perf_stats = self.evaluator.optimizer.get_stats()

        return {
            "total_tasks": total,
            "passed": passed,
            "success_rate": passed / total if total > 0 else 0,
            "total_time": total_time,
            "avg_time": total_time / total if total > 0 else 0,
            "tool_usage": tool_usage,
            "performance": perf_stats,
        }


def create_runner(agent) -> Runner:
    """创建运行器"""
    return Runner(agent)
