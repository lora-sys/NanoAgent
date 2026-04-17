"""NanoAgent CLI - 极简 Agent 框架"""

import asyncio
import sys
from typing import Optional
from dotenv import load_dotenv
import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from core.agent import NanoAgent

load_dotenv()

app = typer.Typer(
    name="nanoagent", help="NanoAgent - 极简 Agent 框架", add_completion=False
)
session_app = typer.Typer(help="会话管理")
app.add_typer(session_app, name="session")


@app.command()
def run(
    task: str = typer.Argument(..., help="任务描述"),
    max_iterations: Optional[int] = typer.Option(
        None, "--max", "-m", help="最大迭代次数（可选）"
    ),
    session_id: Optional[str] = typer.Option(
        None, "--session-id", "-s", help="恢复已有会话"
    ),
    session_name: Optional[str] = typer.Option(
        None, "--session-name", help="创建新会话并命名"
    ),
) -> None:
    """执行任务"""
    try:
        agent = NanoAgent(session_id=session_id, session_name=session_name)
        result = agent.run(task, max_iterations=max_iterations)

        sid = result.get("session_id")
        if sid:
            typer.echo(f"📌 会话: {sid}")

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
def chat(
    session_id: Optional[str] = typer.Option(
        None, "--session-id", "-s", help="恢复已有会话"
    ),
    session_name: Optional[str] = typer.Option(
        None, "--session-name", help="创建新会话并命名"
    ),
) -> None:
    """交互式对话模式"""
    try:
        agent = NanoAgent(session_id=session_id, session_name=session_name)
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


# ---- Session Commands ----


@session_app.command("list")
def session_list(
    limit: int = typer.Option(20, "--limit", "-n", help="显示数量"),
) -> None:
    """列出所有会话"""
    from core.session import get_session_manager

    sm = get_session_manager()
    sessions = sm.list_sessions()
    if not sessions:
        typer.echo("暂无会话记录")
        return

    table = Table(title=f"会话列表 (共 {len(sessions)} 个)")
    table.add_column("ID", style="cyan")
    table.add_column("名称", style="green")
    table.add_column("消息", justify="right")
    table.add_column("任务数", justify="right")
    table.add_column("更新时间", style="dim")

    for s in sessions[:limit]:
        table.add_row(
            s.id,
            s.name,
            str(len(s.messages)),
            str(s.task_count),
            s.updated_at[:19].replace("T", " "),
        )

    console = Console()
    console.print(table)


@session_app.command("new")
def session_new(
    name: str = typer.Argument(..., help="会话名称"),
) -> None:
    """创建新会话"""
    from core.session import get_session_manager

    sm = get_session_manager()
    session = sm.create_session(name=name)
    typer.echo(f"✅ 会话已创建: {session.id} ({session.name})")


@session_app.command("show")
def session_show(
    session_id: str = typer.Argument(..., help="会话 ID"),
) -> None:
    """查看会话详情"""
    from core.session import get_session_manager

    sm = get_session_manager()
    session = sm.get_session(session_id)
    if not session:
        typer.echo(f"会话 {session_id} 不存在", err=True)
        raise typer.Exit(1)

    rprint("[bold]会话信息[/bold]")
    rprint(f"  ID: {session.id}")
    rprint(f"  名称: {session.name}")
    rprint(f"  创建: {session.created_at}")
    rprint(f"  更新: {session.updated_at}")
    rprint(f"  消息数: {len(session.messages)}")
    rprint(f"  任务数: {session.task_count}")
    rprint(f"  Token: {session.total_tokens}")
    rprint("\n[bold]对话内容[/bold]")
    for msg in session.messages:
        role_color = {"system": "dim", "user": "cyan", "assistant": "green"}.get(
            msg.role, "white"
        )
        content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
        rprint(f"  [{role_color}]{msg.role}[/{role_color}]: {content}")


@session_app.command("delete")
def session_delete(
    session_id: str = typer.Argument(..., help="会话 ID"),
) -> None:
    """删除会话"""
    from core.session import get_session_manager

    sm = get_session_manager()
    if sm.delete_session(session_id):
        typer.echo(f"✅ 会话 {session_id} 已删除")
    else:
        typer.echo(f"会话 {session_id} 不存在", err=True)
        raise typer.Exit(1)


@session_app.command("rename")
def session_rename(
    session_id: str = typer.Argument(..., help="会话 ID"),
    new_name: str = typer.Argument(..., help="新名称"),
) -> None:
    """重命名会话"""
    from core.session import get_session_manager

    sm = get_session_manager()
    if sm.rename_session(session_id, new_name):
        typer.echo(f"✅ 会话已重命名为: {new_name}")
    else:
        typer.echo(f"会话 {session_id} 不存在", err=True)
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
