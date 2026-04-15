"""NanoAgent CLI - 极简 Agent 框架"""

from typing import Optional
from dotenv import load_dotenv
import typer
from core.agent import NanoAgent

load_dotenv()

app = typer.Typer(
    name="nanoagent", help="NanoAgent - 极简 Agent 框架", add_completion=False
)


@app.command()
def run(
    task: str = typer.Argument(..., help="任务描述"),
    max_iterations: Optional[int] = typer.Option(
        None, "--max", "-m", help="最大迭代次数（可选）"
    ),
) -> None:
    """执行任务"""
    agent = NanoAgent()
    result = agent.run(task, max_iterations=max_iterations)

    typer.echo(f"✅ 状态: {result.get('status', 'unknown')}")
    typer.echo(f"🔄 迭代: {result.get('iterations', 0)}")
    typer.echo(f"🔧 工具: {', '.join(result.get('tools_used', []))}")
    typer.echo(f"📁 产物: {len(result.get('artifacts', []))} 个")


@app.command()
def chat() -> None:
    """交互式对话模式"""
    agent = NanoAgent()
    agent.chat()


@app.command()
def version() -> None:
    """显示版本信息"""
    typer.echo("NanoAgent v2.0.0 - 极简 Agent 框架")


if __name__ == "__main__":
    app()
