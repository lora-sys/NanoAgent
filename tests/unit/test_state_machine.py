"""Agent State Tests (精简版)."""

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
        "stages": [
            {"id": "stage_1", "status": "active"},
            {"id": "stage_2", "status": "pending"}
        ]
    }
    with open(spec_path, "w") as f:
        json.dump(data, f)
    return str(spec_path)


def test_load_stage(state_file):
    state = AgentState(state_file)
    assert state.get_current_stage() == "stage_1"


def test_update_stage(state_file):
    state = AgentState(state_file)
    state.update_stage("stage_2", "active")
    assert state.get_current_stage() == "stage_2"

    # Reload state
    state2 = AgentState(state_file)
    assert state2.get_current_stage() == "stage_2"
