"""Agent State Tests."""

import json
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.state import AgentState


@pytest.fixture
def state_file(tmp_path: Path) -> str:
    """Create a temporary spec file."""
    spec_path = tmp_path / "manifest.json"
    data = {
        "task": "test_task",
        "current_stage": "stage_1",
        "status": "active",
        "artifacts": [],
        "decisions": [],
    }
    with open(spec_path, "w") as f:
        json.dump(data, f)
    return str(spec_path)


def test_load_state(state_file):
    state = AgentState(state_file)
    assert state.get_current_stage() == "stage_1"
    assert state.get_task() == "test_task"


def test_add_message(state_file):
    state = AgentState(state_file)
    state.add_message("user", "hello")
    assert len(state.messages) == 1
    assert state.messages[0]["role"] == "user"


def test_add_artifact(state_file):
    state = AgentState(state_file)
    state.add_artifact("test.txt", "Test file")
    artifacts = state.get_artifacts()
    assert "test.txt" in artifacts


def test_add_decision(state_file):
    state = AgentState(state_file)
    state.add_decision("use python", "simpler approach")
    decisions = state.get_decisions()
    assert "use python" in decisions


def test_update_stage(state_file):
    state = AgentState(state_file)
    state.update_stage("stage_2", "active")
    assert state.get_current_stage() == "stage_2"


def test_reset(state_file):
    state = AgentState(state_file)
    state.add_message("user", "hello")
    state.reset()
    assert state.step_count == 0
    assert len(state.messages) == 0
