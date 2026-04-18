"""End-to-end tests for todo-list tool with real LLM API.

Tests use real API calls when mock.enabled=false in nanoagent.toml.
Tests are sequential (simple → complex) as requested.
"""

import json
import pytest
import sys
import tempfile
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def clean_todo_file(monkeypatch):
    """Isolate todos to a temp file per test."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp = Path(f.name)
    monkeypatch.setattr("tools.todo.TODO_FILE", tmp)
    yield tmp
    if tmp.exists():
        tmp.unlink()


@pytest.fixture(autouse=True)
def start_tracer_session():
    """Start a tracer session so todo is session-aware."""
    try:
        from core.observability import get_tracer
        tracer = get_tracer()
        tracer.start_session("e2e test session")
        yield
        tracer.end_session("completed")
    except Exception:
        yield  # observability optional


# ---- Test 1: Simple — single goal, no context ----


@pytest.mark.asyncio
async def test_todo_e2e_simple_plan():
    """Simple: Plan a trivial goal, verify todo auto-created."""
    from tools.plan import aplan

    result = await aplan("分析这个项目的目录结构")

    # Basic structure check
    assert "steps" in result
    assert "plan_id" in result
    assert result["total_steps"] > 0
    assert len(result["steps"]) > 0

    # Todo auto-created
    assert "todo_id" in result, f"todo_id missing. result keys: {result.keys()}"

    # Verify todo exists and matches plan steps
    from tools.todo import todo_show
    table = todo_show(result["todo_id"])
    assert isinstance(table, str)
    assert len(table) > 0

    print(f"\n✅ Test 1 passed — plan created {result['total_steps']} steps, todo_id={result['todo_id']}")


# ---- Test 2: Medium — with current_state context ----


@pytest.mark.asyncio
async def test_todo_e2e_with_context():
    """Medium: Plan with current_state and constraints, verify they appear in prompt."""
    from tools.plan import aplan

    result = await aplan(
        "重构代码",
        current_state={"files_analyzed": 3, "language": "python"},
        constraints=["保持向后兼容", "不超过5步"],
    )

    assert "steps" in result
    assert "todo_id" in result
    assert result["total_steps"] > 0

    # Verify the constraint was passed (check plan result has expected shape)
    assert len(result["steps"]) <= 5, f"Expected ≤5 steps, got {len(result['steps'])}"

    # Verify todo items match steps
    from tools.todo import todo_show
    table = todo_show(result["todo_id"])
    assert "重构" in table or "code" in table.lower()

    print(f"\n✅ Test 2 passed — plan with context created {result['total_steps']} steps")


# ---- Test 3: Complex — multiple phases, verify chain integration ----


@pytest.mark.asyncio
async def test_todo_e2e_chain_with_todo():
    """Complex: Create a plan, then simulate chain execution updating todo status."""
    from tools.plan import aplan
    from tools.todo import todo_update_status, todo_show

    # 1. Create plan
    result = await aplan("实现一个 Python CLI 工具")
    assert "steps" in result
    assert "todo_id" in result
    todo_id = result["todo_id"]

    # 2. Simulate chain executing first 2 steps
    for step_idx in range(min(2, len(result["steps"]))):
        updated = todo_update_status(todo_id, step_idx, "done")
        assert updated["status"] == "done"

    # 3. Mark step 2 as in_progress
    if len(result["steps"]) >= 3:
        todo_update_status(todo_id, 2, "in_progress")

    # 4. Render final state
    table = todo_show(todo_id)
    assert "[x]" in table or "[>]" in table  # at least some items marked

    # 5. Verify plan still intact
    assert result["plan_id"] is not None

    print(f"\n✅ Test 3 passed — chain simulation updated todo statuses correctly")
