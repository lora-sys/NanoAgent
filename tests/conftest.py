"""Test fixtures and utilities."""

import sys
from pathlib import Path
from typing import Dict, Any

import pytest

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "agent_workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def sample_spec_data() -> Dict[str, Any]:
    return {
        "overall_goal": "创建一个简单的 Web 应用",
        "deliverables": ["README.md", "main.py", "requirements.txt"],
        "boundaries": {"always": ["使用 Python 3.8+"], "ask_first": [], "never": []},
        "success_criteria": ["应用可以正常运行", "代码符合 PEP 8 规范"],
    }


@pytest.fixture
def sample_context() -> Dict[str, Any]:
    return {
        "current_stage_id": "stage_1",
        "current_stage_spec": "实现基本功能",
        "constraints": {"always": ["使用相对路径"], "never": ["访问系统文件"]},
        "artifacts": [],
        "decisions": [],
    }


@pytest.fixture
def sample_manifest() -> Dict[str, Any]:
    return {
        "project_name": "test_project",
        "current_stage": "stage_1",
        "total_stages": 3,
        "stages": [
            {"stage_id": "stage_1", "name": "需求分析", "status": "completed", "steps": 5},
            {"stage_id": "stage_2", "name": "实现", "status": "in_progress", "steps": 10},
        ],
    }
