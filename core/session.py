"""NanoAgent 跨会话管理 - 持久化对话状态"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _get_db_path() -> Path:
    """获取会话数据库路径"""
    db_path = Path.home() / ".nanoagent"
    db_path.mkdir(parents=True, exist_ok=True)
    return db_path / "sessions.db"


def _init_db() -> None:
    """初始化会话数据库"""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            task_count INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            metadata TEXT DEFAULT '{}',
            system_prompt TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_messages_session
        ON conversation_messages(session_id)
    """)

    conn.commit()
    conn.close()


@dataclass
class SessionMessage:
    """会话消息"""
    id: str
    session_id: str
    role: str
    content: str
    created_at: str

    @classmethod
    def from_row(cls, row: tuple) -> "SessionMessage":
        return cls(
            id=row[0],
            session_id=row[1],
            role=row[2],
            content=row[3],
            created_at=row[4],
        )


@dataclass
class Session:
    """会话"""
    id: str
    name: str
    created_at: str = ""
    updated_at: str = ""
    task_count: int = 0
    total_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    system_prompt: Optional[str] = None
    messages: List[SessionMessage] = field(default_factory=list)

    def __post_init__(self):
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def add_message(self, role: str, content: str) -> SessionMessage:
        """添加消息"""
        msg = SessionMessage(
            id=str(uuid.uuid4())[:8],
            session_id=self.id,
            role=role,
            content=content,
            created_at=datetime.now().isoformat(),
        )
        self.messages.append(msg)
        self.updated_at = datetime.now().isoformat()
        return msg

    def save(self) -> None:
        """保存到数据库"""
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO sessions
                (id, name, created_at, updated_at, task_count, total_tokens, metadata, system_prompt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.id,
                    self.name,
                    self.created_at,
                    self.updated_at,
                    self.task_count,
                    self.total_tokens,
                    json.dumps(self.metadata, ensure_ascii=False),
                    self.system_prompt,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def load_messages(self) -> List[SessionMessage]:
        """加载会话消息"""
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, session_id, role, content, created_at "
            "FROM conversation_messages WHERE session_id = ? ORDER BY created_at ASC",
            (self.id,),
        )
        rows = cursor.fetchall()
        conn.close()
        self.messages = [SessionMessage.from_row(r) for r in rows]
        return self.messages

    def save_messages(self) -> None:
        """保存消息到数据库"""
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            for msg in self.messages:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO conversation_messages
                    (id, session_id, role, content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (msg.id, msg.session_id, msg.role, msg.content, msg.created_at),
                )
            conn.commit()
        finally:
            conn.close()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "task_count": self.task_count,
            "total_tokens": self.total_tokens,
            "metadata": self.metadata,
            "message_count": len(self.messages),
        }

    def get_conversation(self) -> List[Dict[str, str]]:
        """获取对话列表格式"""
        return [{"role": m.role, "content": m.content} for m in self.messages]


class SessionManager:
    """会话管理器 - 单例模式"""

    _instance: Optional["SessionManager"] = None

    def __init__(self):
        _init_db()

    @classmethod
    def get_instance(cls) -> "SessionManager":
        if cls._instance is None:
            cls._instance = SessionManager()
        return cls._instance

    def create_session(
        self,
        name: Optional[str] = None,
        system_prompt: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """创建新会话"""
        session_id = str(uuid.uuid4())[:8]
        session_name = name or f"session-{session_id}"
        session = Session(
            id=session_id,
            name=session_name,
            system_prompt=system_prompt,
            metadata=metadata or {},
        )
        session.save()
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, created_at, updated_at, task_count, total_tokens, metadata, system_prompt "
            "FROM sessions WHERE id = ?",
            (session_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        session = Session(
            id=row[0],
            name=row[1],
            created_at=row[2],
            updated_at=row[3],
            task_count=row[4],
            total_tokens=row[5],
            metadata=json.loads(row[6]) if row[6] else {},
            system_prompt=row[7],
        )
        session.load_messages()
        session.updated_at = datetime.now().isoformat()
        session.save()
        return session

    def list_sessions(
        self, limit: int = 20, include_messages: bool = False
    ) -> List[Session]:
        """列出所有会话"""
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, created_at, updated_at, task_count, total_tokens, metadata, system_prompt "
            "FROM sessions ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()

        sessions = []
        for row in rows:
            session = Session(
                id=row[0],
                name=row[1],
                created_at=row[2],
                updated_at=row[3],
                task_count=row[4],
                total_tokens=row[5],
                metadata=json.loads(row[6]) if row[6] else {},
                system_prompt=row[7],
            )
            if include_messages:
                session.load_messages()
            sessions.append(session)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM conversation_messages WHERE session_id = ?", (session_id,)
            )
            cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            deleted = cursor.rowcount > 0
            conn.commit()
        finally:
            conn.close()
        return deleted

    def rename_session(self, session_id: str, new_name: str) -> bool:
        """重命名会话"""
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE sessions SET name = ?, updated_at = ? WHERE id = ?",
                (new_name, datetime.now().isoformat(), session_id),
            )
            updated = cursor.rowcount > 0
            conn.commit()
        finally:
            conn.close()
        return updated

    def add_tokens(self, session_id: str, tokens: int) -> None:
        """累加 token 计数"""
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE sessions SET total_tokens = total_tokens + ? WHERE id = ?",
                (tokens, session_id),
            )
            conn.commit()
        finally:
            conn.close()

    def increment_task_count(self, session_id: str) -> None:
        """增加任务计数"""
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE sessions SET task_count = task_count + 1, updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), session_id),
            )
            conn.commit()
        finally:
            conn.close()


def get_session_manager() -> SessionManager:
    """获取会话管理器实例"""
    return SessionManager.get_instance()
