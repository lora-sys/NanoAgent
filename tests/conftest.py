"""
测试工具函数和通用 Fixtures
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
import json
from typing import Dict, Any


# ============ 通用 Fixtures ============


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """创建临时工作空间"""
    workspace = tmp_path / "agent_workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def sample_spec_data() -> Dict[str, Any]:
    """示例 Spec 数据"""
    return {
        "overall_goal": "创建一个简单的 Web 应用",
        "deliverables": [
            "README.md - 项目文档",
            "main.py - 主程序文件",
            "requirements.txt - 依赖列表",
        ],
        "boundaries": {
            "always": ["使用 Python 3.8+", "包含错误处理"],
            "ask_first": ["添加外部依赖前确认"],
            "never": ["删除用户文件", "修改系统配置"],
        },
        "success_criteria": ["应用可以正常运行", "代码符合 PEP 8 规范"],
    }


@pytest.fixture
def sample_context() -> Dict[str, Any]:
    """示例上下文数据"""
    return {
        "current_stage_id": "stage_1",
        "current_stage_spec": "实现基本功能",
        "constraints": {"always": ["使用相对路径"], "never": ["访问系统文件"]},
        "artifacts": [],
        "decisions": [],
    }


@pytest.fixture
def sample_manifest() -> Dict[str, Any]:
    """示例 Manifest 数据"""
    return {
        "project_name": "test_project",
        "current_stage": "stage_1",
        "total_stages": 3,
        "stages": [
            {
                "stage_id": "stage_1",
                "name": "需求分析",
                "status": "completed",
                "steps": 5,
            },
            {
                "stage_id": "stage_2",
                "name": "实现",
                "status": "in_progress",
                "steps": 10,
            },
        ],
    }


# ============ 辅助函数 ============


def create_temp_file(workspace: Path, filename: str, content: str) -> Path:
    """在临时工作空间创建文件"""
    file_path = workspace / filename
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")
    return file_path


def load_json_fixture(fixture_name: str) -> Dict[str, Any]:
    """从 fixtures 目录加载 JSON 文件"""
    fixture_path = Path(__file__).parent / "fixtures" / fixture_name
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)
