"""CLI 追踪查看器 - 使用 rich 表格显示追踪数据"""

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from core.observability import list_traces, get_trace, get_stats, delete_trace


console = Console()


def print_trace_list(limit: int = 20) -> None:
    """打印追踪列表"""
    traces = list_traces(limit)

    if not traces:
        console.print("[dim]No traces found[/dim]")
        return

    table = Table(title=f"Recent Traces (last {len(traces)})")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Task", style="white")
    table.add_column("Started", style="green")
    table.add_column("Tokens", justify="right", style="yellow")
    table.add_column("Cost", justify="right", style="magenta")
    table.add_column("Status", style="blue")
    table.add_column("LLM", justify="right")
    table.add_column("Tool", justify="right")

    for t in traces:
        started = t[2][:19] if t[2] else ""
        status = t[6] if len(t) > 6 else ""
        status_color = "green" if status == "completed" else "red"
        table.add_row(
            t[0],                              # ID
            t[1][:40] if t[1] else "",        # Task
            started,                            # Started
            f"{t[3]:,}" if t[3] else "0",    # Tokens
            f"${t[4]:.4f}" if t[4] else "$0", # Cost
            f"[{status_color}]{status}[/{status_color}]",
            f"{t[7]}" if len(t) > 7 else "0",  # LLM calls
            f"{t[8]}" if len(t) > 8 else "0",  # Tool calls
        )

    console.print(table)


def print_trace_detail(trace_id: str) -> None:
    """打印追踪详情"""
    data = get_trace(trace_id)

    if not data:
        console.print(f"[red]Trace {trace_id} not found[/red]")
        return

    trace = data["trace"]
    llm_calls = data["llm_calls"]
    tool_calls = data["tool_calls"]

    # Trace header
    started = trace[2][:19] if trace[2] else ""
    ended = trace[3][:19] if trace[3] else ""
    status = trace[6] if len(trace) > 6 else ""

    console.print(Panel(
        f"[cyan]Task:[/cyan] {trace[1]}\n"
        f"[cyan]Started:[/cyan] {started}\n"
        f"[cyan]Ended:[/cyan] {ended}\n"
        f"[cyan]Status:[/cyan] {status}\n"
        f"[cyan]Total Tokens:[/cyan] {trace[4]:,}\n"
        f"[cyan]Total Cost:[/cyan] ${trace[5]:.6f}\n"
        f"[cyan]LLM Calls:[/cyan] {trace[7]}\n"
        f"[cyan]Tool Calls:[/cyan] {trace[8]}",
        title=f"Trace {trace_id}",
        border_style="cyan",
    ))

    # LLM Calls
    if llm_calls:
        llm_table = Table(title="LLM Calls")
        llm_table.add_column("Model", style="yellow")
        llm_table.add_column("Input", justify="right")
        llm_table.add_column("Output", justify="right")
        llm_table.add_column("Total", justify="right")
        llm_table.add_column("Cost", justify="right")
        llm_table.add_column("Duration", justify="right")

        for call in llm_calls:
            llm_table.add_row(
                call[2],                                # model
                f"{call[3]:,}",                         # input_tokens
                f"{call[4]:,}",                         # output_tokens
                f"{call[5]:,}",                         # total_tokens
                f"${call[6]:.6f}" if call[6] else "$0",
                f"{call[7]}ms",                         # duration_ms
            )
        console.print(llm_table)

    # Tool Calls
    if tool_calls:
        tool_table = Table(title="Tool Calls")
        tool_table.add_column("Tool", style="cyan")
        tool_table.add_column("Duration", justify="right")
        tool_table.add_column("Args", style="dim")
        tool_table.add_column("Error", style="red")

        for call in tool_calls:
            args = call[3][:50] if call[3] else ""
            error = f"[red]{call[7]}[/red]" if call[7] else ""
            tool_table.add_row(
                call[2],                    # tool_name
                f"{call[6]}ms",             # duration_ms
                args,
                error,
            )
        console.print(tool_table)

    # Show last LLM response if available
    if llm_calls:
        last_call = llm_calls[-1]
        output = last_call[10] if len(last_call) > 10 else ""
        if output:
            console.print(Panel(
                Syntax(output[:500] if len(output) > 500 else output, "json"),
                title="Last LLM Response",
                border_style="green",
            ))


def print_stats() -> None:
    """打印统计信息"""
    stats = get_stats()

    console.print(Panel(
        f"[cyan]Total Traces:[/cyan] {stats['total_traces']}\n"
        f"[cyan]Total Tokens:[/cyan] {stats['total_tokens']:,}\n"
        f"[cyan]Total Cost:[/cyan] ${stats['total_cost']:.6f}\n"
        f"[cyan]Total LLM Calls:[/cyan] {stats['total_llm_calls']}\n"
        f"[cyan]Total Tool Calls:[/cyan] {stats['total_tool_calls']}",
        title="Statistics",
        border_style="cyan",
    ))


def delete_trace_by_id(trace_id: str) -> bool:
    """删除追踪"""
    success = delete_trace(trace_id)
    if success:
        console.print(f"[green]Deleted trace {trace_id}[/green]")
    else:
        console.print(f"[red]Trace {trace_id} not found[/red]")
    return success
