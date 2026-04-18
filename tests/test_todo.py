"""Test todo tool."""

import pytest
import sys
import tempfile
from pathlib import Path

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))




@pytest.fixture(autouse=True)
def clean_todo_file(monkeypatch):
    """Use a temp file for each test."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp = Path(f.name)
    monkeypatch.setattr("tools.todo.TODO_FILE", tmp)
    yield tmp
    if tmp.exists():
        tmp.unlink()


class TestTodoCreate:
    """Test todo_create."""

    def test_create_with_items(self, clean_todo_file):
        from tools.todo import todo_create

        result = todo_create("My Plan", ["Step 1", "Step 2", "Step 3"])

        assert result["name"] == "My Plan"
        assert result["plan_id"] is None
        assert len(result["todos"]) == 3
        assert result["todos"][0]["description"] == "Step 1"
        assert result["todos"][0]["status"] == "pending"
        assert result["todos"][0]["step_index"] == 0
        assert result["todos"][2]["step_index"] == 2
        assert result["id"] is not None

    def test_create_empty_items(self, clean_todo_file):
        from tools.todo import todo_create

        result = todo_create("Empty Plan", [])
        assert result["name"] == "Empty Plan"
        assert result["todos"] == []

    def test_create_persists(self, clean_todo_file):
        from tools.todo import todo_create, _load_data

        todo_create("Persisted", ["Item A"])
        data = _load_data()
        assert len(data["lists"]) == 1
        assert data["lists"][0]["name"] == "Persisted"


class TestTodoAdd:
    """Test todo_add."""

    def test_add_to_existing(self, clean_todo_file):
        from tools.todo import todo_add, todo_create

        tl = todo_create("Test List", ["Original"])
        added = todo_add(tl["id"], "New Item")

        assert added["description"] == "New Item"
        assert added["status"] == "pending"
        assert added["step_index"] == 1

    def test_add_to_nonexistent_raises(self, clean_todo_file):
        from tools.todo import todo_add

        with pytest.raises(ValueError, match="not found"):
            todo_add("nonexistent", "New Item")


class TestTodoDone:
    """Test todo_done."""

    def test_mark_done(self, clean_todo_file):
        from tools.todo import todo_done, todo_create

        tl = todo_create("Test", ["Item"])
        item_id = tl["todos"][0]["id"]
        result = todo_done(tl["id"], item_id)

        assert result["status"] == "done"

    def test_done_nonexistent_list_raises(self, clean_todo_file):
        from tools.todo import todo_done

        with pytest.raises(ValueError, match="not found"):
            todo_done("bad_id", "item_id")

    def test_done_nonexistent_item_raises(self, clean_todo_file):
        from tools.todo import todo_create, todo_done

        tl = todo_create("Test", ["Item"])
        with pytest.raises(ValueError, match="not found"):
            todo_done(tl["id"], "bad_item_id")


class TestTodoShow:
    """Test todo_show."""

    def test_show_returns_string(self, clean_todo_file):
        from tools.todo import todo_create, todo_show

        tl = todo_create("Render Test", ["Step 1", "Step 2"])
        output = todo_show(tl["id"])

        assert isinstance(output, str)
        assert "Render Test" in output
        assert "Step 1" in output

    def test_show_nonexistent_raises(self, clean_todo_file):
        from tools.todo import todo_show

        with pytest.raises(ValueError, match="not found"):
            todo_show("bad_id")


class TestTodoListAll:
    """Test todo_list_all."""

    def test_list_empty(self, clean_todo_file):
        from tools.todo import todo_list_all

        assert todo_list_all() == []

    def test_list_returns_summaries(self, clean_todo_file):
        from tools.todo import todo_create, todo_done, todo_list_all

        tl = todo_create("Plan A", ["Step 1", "Step 2", "Step 3"])
        todo_done(tl["id"], tl["todos"][0]["id"])

        summaries = todo_list_all()
        assert len(summaries) == 1
        assert summaries[0]["name"] == "Plan A"
        assert summaries[0]["item_count"] == 3
        assert summaries[0]["done_count"] == 1


class TestTodoDelete:
    """Test todo_delete."""

    def test_delete_existing(self, clean_todo_file):
        from tools.todo import todo_create, todo_delete, todo_list_all

        tl = todo_create("To Delete", ["Item"])
        assert len(todo_list_all()) == 1

        result = todo_delete(tl["id"])
        assert result is True
        assert len(todo_list_all()) == 0

    def test_delete_nonexistent_returns_false(self, clean_todo_file):
        from tools.todo import todo_delete

        assert todo_delete("nonexistent") is False


class TestCreateTodoFromPlan:
    """Test create_todo_from_plan."""

    def test_creates_todo_from_steps(self, clean_todo_file):
        from tools.todo import create_todo_from_plan

        plan_result = {
            "steps": [
                {"step": 1, "description": "Read files"},
                {"step": 2, "description": "Analyze code"},
            ],
            "plan_id": "abc123",
            "total_steps": 2,
        }

        todo = create_todo_from_plan(plan_result, "Test Plan")

        assert todo is not None
        assert todo["name"] == "Test Plan"
        assert todo["plan_id"] == "abc123"
        assert len(todo["todos"]) == 2

    def test_returns_none_for_empty_steps(self, clean_todo_file):
        from tools.todo import create_todo_from_plan

        result = create_todo_from_plan({"steps": []}, "Empty")
        assert result is None


class TestTodoUpdateStatus:
    """Test todo_update_status."""

    def test_update_to_in_progress(self, clean_todo_file):
        from tools.todo import todo_create, todo_update_status

        tl = todo_create("Test", ["Step 1", "Step 2"])
        result = todo_update_status(tl["id"], 0, "in_progress")

        assert result["status"] == "in_progress"

    def test_invalid_status_raises(self, clean_todo_file):
        from tools.todo import todo_create, todo_update_status

        tl = todo_create("Test", ["Step 1"])
        with pytest.raises(ValueError, match="Invalid status"):
            todo_update_status(tl["id"], 0, "bad_status")

    def test_nonexistent_list_raises(self, clean_todo_file):
        from tools.todo import todo_update_status

        with pytest.raises(ValueError, match="not found"):
            todo_update_status("bad_id", 0, "done")

    def test_nonexistent_step_raises(self, clean_todo_file):
        from tools.todo import todo_create, todo_update_status

        tl = todo_create("Test", ["Step 1"])
        with pytest.raises(ValueError, match="step_index"):
            todo_update_status(tl["id"], 99, "done")
