"""Todo list tool - track sub-tasks during planning/execution."""

import json
import uuid
from pathlib import Path
from typing import Optional

TODO_FILE = Path.home() / ".nanoagent" / "todos.json"


def _get_session_id() -> Optional[str]:
    """Get current session ID from Tracer singleton if available."""
    try:
        from core.observability import get_tracer
        tracer = get_tracer()
        session = tracer.get_current_session()
        return session.id if session else None
    except Exception:
        return None


def _load_data() -> dict:
    """Load todos from file, create if missing."""
    if not TODO_FILE.exists():
        return {"lists": []}
    with open(TODO_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    if not content.strip():
        return {"lists": []}
    return json.loads(content)


def _save_data(data: dict) -> None:
    """Save todos to file."""
    TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def todo_create(name: str, items: list[str], session_id: Optional[str] = None) -> dict:
    """Create a new todo list with items.

    Args:
        name: Name of the todo list.
        items: List of item descriptions.
        session_id: Optional session ID. Defaults to current Tracer session.
    """
    if session_id is None:
        session_id = _get_session_id()

    todo_list = {
        "id": str(uuid.uuid4())[:8],
        "session_id": session_id,
        "plan_id": None,
        "name": name,
        "todos": [
            {
                "id": str(uuid.uuid4())[:8],
                "description": item,
                "status": "pending",
                "step_index": idx,
            }
            for idx, item in enumerate(items)
        ],
    }
    data = _load_data()
    data["lists"].append(todo_list)
    _save_data(data)
    return todo_list


def todo_add(list_id: str, item: str) -> dict:
    """Add item to an existing todo list."""
    data = _load_data()
    todo_list = next((lst for lst in data["lists"] if lst["id"] == list_id), None)
    if not todo_list:
        raise ValueError(f"TodoList {list_id} not found")

    todo_item = {
        "id": str(uuid.uuid4())[:8],
        "description": item,
        "status": "pending",
        "step_index": len(todo_list["todos"]),
    }
    todo_list["todos"].append(todo_item)
    _save_data(data)
    return todo_item


def todo_done(list_id: str, item_id: str) -> dict:
    """Mark a todo item as done."""
    data = _load_data()
    todo_list = next((lst for lst in data["lists"] if lst["id"] == list_id), None)
    if not todo_list:
        raise ValueError(f"TodoList {list_id} not found")

    todo_item = next((t for t in todo_list["todos"] if t["id"] == item_id), None)
    if not todo_item:
        raise ValueError(f"TodoItem {item_id} not found")

    todo_item["status"] = "done"
    _save_data(data)
    return todo_item


def todo_update_status(list_id: str, step_index: int, status: str) -> dict:
    """Update todo item status by step_index."""
    valid_statuses = ("pending", "in_progress", "done")
    if status not in valid_statuses:
        raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")

    data = _load_data()
    todo_list = next((lst for lst in data["lists"] if lst["id"] == list_id), None)
    if not todo_list:
        raise ValueError(f"TodoList {list_id} not found")

    todo_item = next(
        (t for t in todo_list["todos"] if t.get("step_index") == step_index),
        None,
    )
    if not todo_item:
        raise ValueError(f"No todo item with step_index {step_index}")

    todo_item["status"] = status
    _save_data(data)
    return todo_item


def todo_show(list_id: str) -> str:
    """Render todo list as a Rich table string."""
    from io import StringIO

    from rich.console import Console
    from rich.table import Table

    data = _load_data()
    todo_list = next((lst for lst in data["lists"] if lst["id"] == list_id), None)
    if not todo_list:
        raise ValueError(f"TodoList {list_id} not found")

    table = Table(title=f"Todo: {todo_list['name']}", show_lines=True)
    table.add_column("Status", style="cyan", width=8)
    table.add_column("Step", justify="right", style="yellow", width=4)
    table.add_column("Description", style="white")

    for item in todo_list["todos"]:
        status_icon = {
            "pending": "[ ]",
            "in_progress": "[>]",
            "done": "[x]",
        }.get(item["status"], "[?]")
        step = (
            str(item.get("step_index", ""))
            if item.get("step_index") is not None
            else ""
        )
        desc_style = "dim" if item["status"] == "done" else "white"
        table.add_row(status_icon, step, f"[{desc_style}]{item['description']}[/{desc_style}]")

    output = StringIO()
    console = Console(file=output, force_terminal=True)
    console.print(table)
    return output.getvalue()


def todo_list_all(session_id: Optional[str] = None) -> list[dict]:
    """List all todo lists, optionally filtered by session.

    Args:
        session_id: If provided, only return todo lists for this session.
                    If None, returns lists for the current Tracer session.
                    If "all", returns all lists regardless of session.
    """
    data = _load_data()

    if session_id == "all":
        lists = data["lists"]
    elif session_id is None:
        current = _get_session_id()
        lists = [lst for lst in data["lists"] if lst.get("session_id") == current]
    else:
        lists = [lst for lst in data["lists"] if lst.get("session_id") == session_id]

    return [
        {
            "id": lst["id"],
            "name": lst["name"],
            "plan_id": lst.get("plan_id"),
            "session_id": lst.get("session_id"),
            "item_count": len(lst["todos"]),
            "done_count": sum(1 for t in lst["todos"] if t["status"] == "done"),
        }
        for lst in lists
    ]


def todo_delete(list_id: str) -> bool:
    """Delete a todo list."""
    data = _load_data()
    original_len = len(data["lists"])
    data["lists"] = [lst for lst in data["lists"] if lst["id"] != list_id]
    if len(data["lists"]) == original_len:
        return False
    _save_data(data)
    return True


def create_todo_from_plan(plan_result: dict, plan_name: str = "Plan") -> Optional[dict]:
    """Create a todo list from plan() or aplan() result.

    Captures the current Tracer session ID automatically.
    """
    steps = plan_result.get("steps", [])
    if not steps:
        return None

    plan_id = plan_result.get("plan_id")
    session_id = _get_session_id()

    items = [
        step.get("description", f"Step {step.get('step', i)}")
        for i, step in enumerate(steps)
    ]

    todo_list = todo_create(plan_name, items, session_id=session_id)

    if plan_id:
        data = _load_data()
        for lst in data["lists"]:
            if lst["id"] == todo_list["id"]:
                lst["plan_id"] = plan_id
                todo_list["plan_id"] = plan_id
                break
        _save_data(data)

    return todo_list
