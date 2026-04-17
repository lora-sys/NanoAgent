"""评估运行脚本 - 执行 nanoagent 框架的全面评估

使用方法:
    python tests/run_evaluation.py              # 运行所有评估
    python tests/run_evaluation.py --basic      # 只运行基础任务
    python tests/run_evaluation.py --advanced   # 只运行高级任务
    python tests/run_evaluation.py --report     # 生成详细报告
"""

import sys
import json
import argparse
from datetime import datetime

from core.agent import NanoAgent
from core.evaluation import EvaluationRunner, EvaluationAnalyzer
from tests.evaluation_tasks import get_evaluation_tasks, get_all_evaluation_tasks


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="运行 nanoagent 评估套件")
    parser.add_argument(
        "--category",
        choices=[
            "basic",
            "intermediate",
            "advanced",
            "expert",
            "tool_specific",
            "edge_cases",
            "all",
        ],
        default="all",
        help="选择要运行的评估类别",
    )
    parser.add_argument("--output", type=str, help="输出报告文件路径")
    parser.add_argument(
        "--format", choices=["json", "text", "both"], default="both", help="输出格式"
    )
    parser.add_argument("--verbose", action="store_true", help="详细输出模式")
    return parser.parse_args()


def run_evaluation(args):
    """运行评估"""
    print("🚀 NanoAgent 评估系统")
    print("=" * 80)
    print(f"📅 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 评估类别: {args.category}")
    print()

    # 初始化代理
    print("🤖 初始化 NanoAgent...")
    agent = NanoAgent()

    # 获取评估任务
    all_tasks = get_all_evaluation_tasks()

    if args.category == "all":
        tasks = get_evaluation_tasks()
    else:
        tasks = all_tasks.get(args.category, [])

    if not tasks:
        print(f"❌ 没有找到 '{args.category}' 类别的任务")
        return None

    print(f"📊 加载了 {len(tasks)} 个评估任务")
    print()

    # 创建评估运行器
    runner = EvaluationRunner(agent)

    # 运行评估
    results = runner.run_evaluation_suite(tasks)

    # 分析结果
    print("\n🔍 分析评估结果...")
    analysis = EvaluationAnalyzer.analyze_results(results)

    # 组合完整报告
    full_report = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "agent_version": "1.0.0",
            "evaluation_category": args.category,
            "total_tasks": len(tasks),
        },
        "summary": results["summary"],
        "analysis": analysis,
        "detailed_results": results["tasks"],
    }

    # 输出报告
    if args.format in ["text", "both"]:
        print_text_report(full_report, args.verbose)

    if args.format in ["json", "both"]:
        output_file = (
            args.output
            or f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        save_json_report(full_report, output_file)
        print(f"\n💾 JSON 报告已保存到: {output_file}")

    return full_report


def print_text_report(report: dict, verbose: bool = False):
    """打印文本格式报告"""
    print("\n" + "=" * 80)
    print("📊 评估报告")
    print("=" * 80)

    summary = report["summary"]
    analysis = report["analysis"]

    # 基本信息
    print(f"\n📅 评估时间: {report['metadata']['timestamp']}")
    print(f"📊 总任务数: {summary['total_tasks']}")
    print(f"✅ 成功任务: {summary['successful_tasks']}")
    print(f"📈 成功率: {summary['success_rate']:.1%}")
    print(f"⏱️ 总时间: {summary['total_time']:.2f}秒")
    print(f"🕐 平均时间: {summary['average_time_per_task']:.2f}秒")

    # 难度统计
    print("\n📊 按难度统计:")
    for difficulty, stats in summary["difficulty_stats"].items():
        pass_rate = stats["passed"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"  {difficulty}: {stats['passed']}/{stats['total']} ({pass_rate:.1f}%)")

    # 工具使用统计
    print("\n🔧 工具使用统计:")
    for tool, count in summary["tool_usage"].items():
        print(f"  {tool}: {count} 次")

    # 性能分析
    perf = analysis["performance_analysis"]
    print("\n⚡ 性能分析:")
    print(f"  平均执行时间: {perf['average_execution_time']:.2f}秒")
    print(f"  平均迭代次数: {perf['average_iterations']:.1f}次")
    print(f"  平均工具调用: {perf['average_tool_calls']:.1f}次")

    # 错误分析
    errors = analysis["error_analysis"]
    if errors["failed_tasks"]:
        print(f"\n❌ 失败任务 ({len(errors['failed_tasks'])}):")
        for task in errors["failed_tasks"]:
            print(f"  - {task}")

    if errors["error_list"] and verbose:
        print("\n🔍 错误详情:")
        for error in errors["error_list"]:
            print(f"  任务: {error['task']}")
            print(f"  错误: {error['error']}")
            print()

    # 改进建议
    suggestions = analysis["improvement_suggestions"]
    if suggestions:
        print("\n💡 改进建议:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")

    # 详细结果
    if verbose:
        print("\n" + "=" * 80)
        print("📋 详细任务结果")
        print("=" * 80)

        for result in report["detailed_results"]:
            task = result["task"]
            verification = result.get("verification", {})
            metrics = result.get("metrics", {})

            print(f"\n🎯 任务: {task['name']}")
            print(f"📝 描述: {task['description']}")
            print(f"📊 难度: {task['difficulty']}")
            print(f"✅ 状态: {'通过' if verification.get('passed', False) else '失败'}")
            print(f"🔧 工具: {metrics.get('tools_used', [])}")
            print(f"⏱️ 时间: {metrics.get('total_time', 0):.2f}秒")
            print(f"🔄 迭代: {metrics.get('iterations', 0)}次")

    print("\n" + "=" * 80)


def save_json_report(report: dict, output_file: str):
    """保存 JSON 格式报告"""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def main():
    """主函数"""
    args = parse_arguments()

    try:
        report = run_evaluation(args)

        if report:
            print("\n✅ 评估完成！")

            # 返回退出码
            success_rate = report["summary"]["success_rate"]
            if success_rate >= 0.8:
                sys.exit(0)  # 成功
            elif success_rate >= 0.5:
                sys.exit(1)  # 警告
            else:
                sys.exit(2)  # 失败
        else:
            print("\n❌ 评估失败")
            sys.exit(2)

    except KeyboardInterrupt:
        print("\n\n⚠️ 评估被用户中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 评估过程中发生错误: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
