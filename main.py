"""NanoAgent CLI"""

from dotenv import load_dotenv
import typer
from core.agent import NanoAgent

load_dotenv()

app = typer.Typer(
    name="nanoagent", help="NanoAgent - 智能任务执行系统", add_completion=False
)


@app.command()
def run(task: str = typer.Argument(..., help="任务描述")) -> None:
    agent = NanoAgent()
    result = agent.run(task)
    typer.echo(f"状态: {result.get('status', 'unknown')}")
    typer.echo(f"步骤: {result.get('steps_executed', 0)}")


@app.command()
def version() -> None:
    typer.echo("NanoAgent v1.0.0")


if __name__ == "__main__":
    app()
