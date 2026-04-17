"""NanoAgent CLI - 极简 Agent 框架"""

import asyncio
import sys
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
    try:
        agent = NanoAgent()
        result = agent.run(task, max_iterations=max_iterations)

        typer.echo(f"✅ 状态: {result.get('status', 'unknown')}")
        typer.echo(f"🔄 迭代: {result.get('iterations', 0)}")
        typer.echo(f"🔧 工具: {', '.join(result.get('tools_used', []))}")
        typer.echo(f"📁 产物: {len(result.get('artifacts', []))} 个")
    finally:
        # 确保事件循环正确清理
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.close()
        except RuntimeError:
            pass


@app.command()
def chat() -> None:
    """交互式对话模式"""
    try:
        agent = NanoAgent()
        agent.chat()
    finally:
        # 确保事件循环正确清理
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.close()
        except RuntimeError:
            pass


@app.command()
def trace(
    action: str = typer.Argument(..., help="操作: list, show, stats, delete"),
    trace_id: Optional[str] = typer.Argument(None, help="追踪 ID"),
    limit: int = typer.Option(20, "--limit", "-n", help="显示数量"),
) -> None:
    """查看追踪记录"""
    from cli.observer import (
        print_trace_list,
        print_trace_detail,
        print_stats,
        delete_trace_by_id,
    )

    if action == "list":
        print_trace_list(limit)
    elif action == "show":
        if not trace_id:
            typer.echo("Error: trace_id required for show", err=True)
            raise typer.Exit(1)
        print_trace_detail(trace_id)
    elif action == "stats":
        print_stats()
    elif action == "delete":
        if not trace_id:
            typer.echo("Error: trace_id required for delete", err=True)
            raise typer.Exit(1)
        delete_trace_by_id(trace_id)
    else:
        typer.echo(f"Unknown action: {action}", err=True)
        typer.echo(
            "Usage: nanoagent trace [list|show|stats|delete] [trace_id]", err=True
        )
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """显示版本信息"""
    typer.echo("NanoAgent v2.0.0 - 极简 Agent 框架")


if __name__ == "__main__":
    try:
        app()
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        # 确保资源正确清理
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.close()
        except RuntimeError:
            pass
