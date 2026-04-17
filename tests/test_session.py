"""测试跨会话管理功能"""

import pytest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import patch

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


# 用临时目录隔离测试数据库
@pytest.fixture(autouse=True)
def temp_session_db(tmp_path, monkeypatch):
    """所有测试使用临时数据库"""
    temp_db_dir = tmp_path / ".nanoagent"
    temp_db_dir.mkdir(parents=True, exist_ok=True)

    # patch _get_db_path 返回临时路径
    import core.session as session_module

    def _temp_db_path():
        return temp_db_dir / "sessions.db"

    monkeypatch.setattr(session_module, "_get_db_path", _temp_db_path)
    # 清除单例
    session_module.SessionManager._instance = None
    yield
    session_module.SessionManager._instance = None


class TestSessionManager:
    """测试会话管理器"""

    def test_create_session(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        session = sm.create_session(name="test-session")

        assert session.id is not None
        assert len(session.id) == 8
        assert session.name == "test-session"
        assert session.task_count == 0
        assert session.total_tokens == 0
        assert len(session.messages) == 0

    def test_create_session_with_system_prompt(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        session = sm.create_session(
            name="with-prompt",
            system_prompt="你是一个测试助手",
            metadata={"env": "test"},
        )

        assert session.system_prompt == "你是一个测试助手"
        assert session.metadata["env"] == "test"

    def test_get_session(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        created = sm.create_session(name="get-test")

        retrieved = sm.get_session(created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "get-test"

    def test_get_nonexistent_session(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        result = sm.get_session("nonexist")
        assert result is None

    def test_list_sessions(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        sm.create_session(name="session-1")
        sm.create_session(name="session-2")
        sm.create_session(name="session-3")

        sessions = sm.list_sessions()
        assert len(sessions) == 3
        # 按更新时间倒序
        names = [s.name for s in sessions]
        assert "session-3" in names
        assert "session-1" in names

    def test_list_sessions_with_limit(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        for i in range(5):
            sm.create_session(name=f"session-{i}")

        sessions = sm.list_sessions(limit=3)
        assert len(sessions) == 3

    def test_delete_session(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        session = sm.create_session(name="delete-test")

        assert sm.get_session(session.id) is not None
        assert sm.delete_session(session.id) is True
        assert sm.get_session(session.id) is None

    def test_delete_nonexistent_session(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        assert sm.delete_session("nonexist") is False

    def test_rename_session(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        session = sm.create_session(name="old-name")

        assert sm.rename_session(session.id, "new-name") is True
        retrieved = sm.get_session(session.id)
        assert retrieved.name == "new-name"

    def test_rename_nonexistent_session(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        assert sm.rename_session("nonexist", "new-name") is False

    def test_increment_task_count(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        session = sm.create_session(name="counter-test")
        assert session.task_count == 0

        sm.increment_task_count(session.id)
        sm.increment_task_count(session.id)
        sm.increment_task_count(session.id)

        retrieved = sm.get_session(session.id)
        assert retrieved.task_count == 3

    def test_add_tokens(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        session = sm.create_session(name="token-test")
        assert session.total_tokens == 0

        sm.add_tokens(session.id, 1000)
        sm.add_tokens(session.id, 500)

        retrieved = sm.get_session(session.id)
        assert retrieved.total_tokens == 1500


class TestSessionMessage:
    """测试会话消息"""

    def test_add_message(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        session = sm.create_session(name="msg-test")

        msg1 = session.add_message("user", "你好")
        msg2 = session.add_message("assistant", "你好！有什么可以帮你？")

        assert len(session.messages) == 2
        assert msg1.role == "user"
        assert msg1.content == "你好"
        assert msg2.role == "assistant"

    def test_save_and_load_messages(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        session = sm.create_session(name="persist-test")

        session.add_message("system", "你是一个助手")
        session.add_message("user", "你好")
        session.add_message("assistant", "你好！")
        session.save()
        session.save_messages()

        # 重新加载
        session2 = sm.get_session(session.id)
        assert len(session2.messages) == 3
        assert session2.messages[0].role == "system"
        assert session2.messages[0].content == "你是一个助手"
        assert session2.messages[1].role == "user"
        assert session2.messages[2].role == "assistant"

    def test_get_conversation(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        session = sm.create_session(name="conv-test")

        session.add_message("system", "sys")
        session.add_message("user", "hello")
        session.add_message("assistant", "hi there")

        conv = session.get_conversation()
        assert len(conv) == 3
        assert conv[0] == {"role": "system", "content": "sys"}
        assert conv[1] == {"role": "user", "content": "hello"}

    def test_to_dict(self):
        from core.session import get_session_manager

        sm = get_session_manager()
        session = sm.create_session(name="dict-test")
        session.add_message("user", "hello")

        data = session.to_dict()
        assert data["id"] == session.id
        assert data["name"] == "dict-test"
        assert data["task_count"] == 0
        assert data["message_count"] == 1
        assert "created_at" in data
        assert "updated_at" in data


class TestNanoAgentWithSession:
    """测试 NanoAgent 与会话集成"""

    def test_agent_create_session(self, temp_session_db):
        from core.agent import NanoAgent

        agent = NanoAgent(session_name="agent-test")
        assert agent.session is not None
        assert agent.session.name == "agent-test"
        assert len(agent.conversation) == 1
        assert agent.conversation[0]["role"] == "system"

    def test_agent_resume_session(self, temp_session_db):
        from core.agent import NanoAgent
        from core.session import get_session_manager

        # 先创建 session 并添加消息
        sm = get_session_manager()
        session = sm.create_session(name="resume-test")
        session.add_message("system", "你是助手")
        session.add_message("user", "之前的对话")
        session.add_message("assistant", "之前的回复")
        session.save_messages()

        # 恢复会话
        agent = NanoAgent(session_id=session.id)
        assert agent.session is not None
        assert len(agent.conversation) == 3
        assert agent.conversation[0]["role"] == "system"
        assert agent.conversation[1]["content"] == "之前的对话"

    def test_agent_no_session(self, temp_session_db):
        from core.agent import NanoAgent

        agent = NanoAgent()
        assert agent.session is None
        assert len(agent.conversation) == 0

    def test_agent_resume_nonexistent_session(self, temp_session_db):
        from core.agent import NanoAgent

        agent = NanoAgent(session_id="nonexist")
        assert agent.session is None
        assert len(agent.conversation) == 0

    def test_run_with_session_persists_messages(self, temp_session_db):
        from core.agent import NanoAgent
        from core.session import get_session_manager

        # mock LLM client
        mock_client = type("MockLLM", (), {
            "chat": lambda self, msgs: '<response>完成了</response>'
        })()

        agent = NanoAgent(session_name="run-test", llm_client=mock_client)
        result = agent.run("简单任务")

        assert result["session_id"] is not None
        assert result["status"] in ("completed", "failed")

        # 验证消息已持久化
        sm = get_session_manager()
        session = sm.get_session(result["session_id"])
        assert len(session.messages) > 0
        # 至少应该包含 system + user + assistant
        roles = [m.role for m in session.messages]
        assert "system" in roles
        assert "user" in roles


class TestSessionManagerSingleton:
    """测试单例模式"""

    def test_singleton(self, temp_session_db):
        from core.session import get_session_manager

        sm1 = get_session_manager()
        sm2 = get_session_manager()
        assert sm1 is sm2
