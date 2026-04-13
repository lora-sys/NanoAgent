"""测试 AgentState 同步更新逻辑"""

import os
import sys
import json
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agent_state import AgentState
from core.agent_loop import NanoAgent

# Mock objects
class MockExecutor:
    def save_context(self, ctx):
        pass

def test_save_step_context():
    """验证 _save_step_context 是否正确更新了内存中的 artifacts"""
    
    # 1. 准备环境
    state = AgentState(manifest_path="/tmp/test_manifest.json")
    agent = NanoAgent.__new__(NanoAgent)
    agent.state = state
    agent.executor = MockExecutor()

    # 模拟：Agent 思考写了一个文件，并且执行成功了
    think_result = {"reason": "Decided to write a config file to initialize the project."}
    action_result = "Successfully wrote 150 chars to package.json" # 模拟执行成功的返回字符串
    observation = "File written successfully"

    # 2. 执行逻辑
    agent._save_step_context(think_result, action_result, observation)

    # 3. 验证结果
    artifacts = state.get_artifacts()
    decisions = state.get_decisions()

    print(f"Artifacts in memory: {artifacts}")
    print(f"Decisions in memory: {decisions}")

    assert "package.json" in artifacts, f"Expected 'package.json' in artifacts, got {artifacts}"
    assert len(decisions) > 0, "Expected decisions to be recorded"
    print("✅ 测试通过！内存状态同步成功。")

if __name__ == "__main__":
    test_save_step_context()
