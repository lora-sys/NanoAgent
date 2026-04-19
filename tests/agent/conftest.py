"""pytest fixtures and configuration for agent tests."""

import pytest

from tests.agent.harness import AgentTestHarness, _run_mode_store
from tests.agent.markers import UNIT, INTEGRATION


def pytest_runtest_setup(item):
    """根据 marker 设置测试模式。"""
    if item.get_closest_marker(UNIT):
        _run_mode_store["mode"] = "mock"
    elif item.get_closest_marker(INTEGRATION):
        _run_mode_store["mode"] = "real"
    else:
        _run_mode_store["mode"] = "auto"


@pytest.fixture
def agent_harness():
    """返回 AgentTestHarness 实例，mode 由 marker 自动决定。"""
    mode = _run_mode_store.get("mode", "auto")
    harness = AgentTestHarness(mode=mode)
    yield harness
    _run_mode_store["mode"] = "auto"


@pytest.fixture
def mock_agent():
    """强制 mock 模式的 harness。"""
    return AgentTestHarness(mode="mock")


@pytest.fixture
def real_agent():
    """强制 real 模式的 harness。"""
    return AgentTestHarness(mode="real")
