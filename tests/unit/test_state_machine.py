"""Agent State Tests (Manifest-driven)."""

import sys
import json
import pytest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.agent_state import AgentState


@pytest.fixture
def manifest_file(tmp_path: Path) -> str:
    """Create a temporary manifest file."""
    manifest_path = tmp_path / "manifest.json"
    data = {
        "project_name": "test_project",
        "current_stage": "stage_1",
        "status": "active",
        "pipeline": [
            {"id": "stage_1", "status": "active"},
            {"id": "stage_2", "status": "pending"}
        ]
    }
    with open(manifest_path, "w") as f:
        json.dump(data, f)
    return str(manifest_path)


def test_load_stage(manifest_file):
    state = AgentState(manifest_file)
    assert state.current_stage == "stage_1"
    assert state.status == "active"


def test_update_stage(manifest_file):
    state = AgentState(manifest_file)
    state.update_stage_status("stage_2", "active")
    
    # Reload state
    state._memory_cache = None
    assert state.current_stage == "stage_2"
    
    # Check file content
    with open(manifest_file) as f:
        data = json.load(f)
        assert data["pipeline"][1]["status"] == "active"
