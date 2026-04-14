"""NanoAgent CLI entry point."""

from dotenv import load_dotenv

load_dotenv()

import typer
from core.agent_loop import NanoAgent

app = typer.Typer(
    name="nanoagent",
    help="NanoAgent - 智能任务执行系统",
    add_completion=False,
)

DEFAULT_TASK = (
    "我要为一个名为'SmartHome AI'的智能家居公司开发一个完整的商业计划书和产品展示网站。"
    "具体需求："
    "1. 核心业务：智能家居控制系统，包括语音助手、设备联动、自动化场景"
    "2. 目标受众：投资人和潜在合作伙伴"
    "3. 前端用途：产品演示和商业展示"
    "4. 技术栈：React + TypeScript"
    "5. 设计风格：现代科技感，蓝色主题"
    "6. 功能要求："
    "- 首页展示产品核心功能"
    "- 产品特性介绍页面"
    "- 技术架构图展示"
    "- 联系我们表单（带验证）"
    "- 响应式设计"
    "7. 交付格式：完整的 React 项目代码 + 部署说明文档"
)


@app.command()
def run(
    task: str = typer.Argument(
        DEFAULT_TASK,
        help="任务描述",
    ),
) -> None:
    """执行 AI 代理任务。

    示例:
        nanoagent run "帮我写一个 Python 快速排序"
        nanoagent run "分析这份数据并生成报告"
    """
    agent = NanoAgent()
    result = agent.run(task)

    # 打印关键结果
    typer.echo("\n" + "=" * 60)
    typer.echo("执行结果摘要")
    typer.echo("=" * 60)
    typer.echo(f"状态: {result.get('status', 'unknown')}")
    typer.echo(f"步骤数: {result.get('steps_executed', 0)}")
    typer.echo(f"交付物: {', '.join(result.get('artifacts', ['无']))}")
    typer.echo("=" * 60)


@app.command()
def version() -> None:
    """显示版本信息。"""
    typer.echo("NanoAgent v1.0.0")


if __name__ == "__main__":
    app()
