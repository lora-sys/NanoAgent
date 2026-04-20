"""NanoAgent 可观测性模块 - 追踪 AI 调用、工具调用、成本统计"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def _get_db_path() -> Path:
    """获取数据库路径"""
    db_path = Path.home() / ".nanoagent"
    db_path.mkdir(parents=True, exist_ok=True)
    return db_path / "traces.db"


def _init_db() -> None:
    """初始化数据库"""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traces (
            id TEXT PRIMARY KEY,
            task TEXT,
            started_at TEXT,
            ended_at TEXT,
            total_tokens INTEGER DEFAULT 0,
            total_cost REAL DEFAULT 0.0,
            status TEXT,
            llm_calls INTEGER DEFAULT 0,
            tool_calls INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS llm_calls (
            id TEXT PRIMARY KEY,
            trace_id TEXT,
            model TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            cost REAL DEFAULT 0.0,
            duration_ms INTEGER DEFAULT 0,
            created_at TEXT,
            input_messages TEXT,
            output_message TEXT,
            FOREIGN KEY (trace_id) REFERENCES traces(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tool_calls (
            id TEXT PRIMARY KEY,
            trace_id TEXT,
            tool_name TEXT,
            args TEXT,
            result TEXT,
            duration_ms INTEGER DEFAULT 0,
            created_at TEXT,
            error TEXT,
            FOREIGN KEY (trace_id) REFERENCES traces(id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_llm_calls_trace
        ON llm_calls(trace_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_tool_calls_trace
        ON tool_calls(trace_id)
    """)

    conn.commit()
    conn.close()


@dataclass
class LLMRecord:
    """LLM 调用记录"""

    id: str
    trace_id: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    duration_ms: int = 0
    created_at: str = ""
    input_messages: str = ""
    output_message: str = ""

    def to_tuple(self):
        return (
            self.id,
            self.trace_id,
            self.model,
            self.input_tokens,
            self.output_tokens,
            self.total_tokens,
            self.cost,
            self.duration_ms,
            self.created_at,
            self.input_messages,
            self.output_message,
        )


@dataclass
class ToolRecord:
    """工具调用记录"""

    id: str
    trace_id: str
    tool_name: str
    args: str = ""
    result: str = ""
    duration_ms: int = 0
    created_at: str = ""
    error: str = ""

    def to_tuple(self):
        """返回批量插入用的 tuple。"""
        return (
            self.id,
            self.trace_id,
            self.tool_name,
            self.args,
            self.result,
            self.duration_ms,
            self.created_at,
            self.error,
        )


@dataclass
class TraceSession:
    """追踪会话"""

    id: str
    task: str
    started_at: str = ""
    ended_at: str = ""
    total_tokens: int = 0
    total_cost: float = 0.0
    status: str = "running"
    llm_calls_count: int = 0
    tool_calls_count: int = 0
    llm_records: list = field(default_factory=list)
    tool_records: list = field(default_factory=list)

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now().isoformat()

    def end(self, status: str = "completed") -> None:
        """结束追踪会话"""
        self.ended_at = datetime.now().isoformat()
        self.status = status

    def add_llm_call(self, record: LLMRecord) -> None:
        """添加 LLM 调用"""
        self.total_tokens += record.total_tokens
        self.total_cost += record.cost
        self.llm_calls_count += 1
        self.llm_records.append(record)

    def add_tool_call(self, record: ToolRecord) -> None:
        """添加工具调用"""
        self.tool_calls_count += 1
        self.tool_records.append(record)

    def save(self) -> None:
        """保存到数据库"""
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO traces
                (id, task, started_at, ended_at, total_tokens, total_cost,
                 status, llm_calls, tool_calls)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    self.id,
                    self.task,
                    self.started_at,
                    self.ended_at,
                    self.total_tokens,
                    self.total_cost,
                    self.status,
                    self.llm_calls_count,
                    self.tool_calls_count,
                ),
            )
            conn.commit()
        finally:
            conn.close()


class Tracer:
    """追踪器 - 单例模式"""

    _instance: Optional["Tracer"] = None

    def __init__(self):
        self._current_session: Optional[TraceSession] = None
        _init_db()

    @classmethod
    def get_instance(cls) -> "Tracer":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = Tracer()
        return cls._instance

    def start_session(self, task: str) -> TraceSession:
        """开始新的追踪会话"""
        session = TraceSession(id=str(uuid.uuid4())[:8], task=task)
        self._current_session = session
        return session

    def end_session(self, status: str = "completed") -> None:
        """结束当前追踪会话"""
        if self._current_session:
            self._current_session.end(status)
            self.flush()  # 批量保存所有记录
            self._current_session.save()
            self._current_session = None

    def get_current_session(self) -> Optional[TraceSession]:
        """获取当前会话"""
        return self._current_session

    def record_llm(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
        input_messages: list,
        output_message: str,
        cost: float = 0.0,
    ) -> Optional[LLMRecord]:
        """记录 LLM 调用"""
        if not self._current_session:
            return None

        record = LLMRecord(
            id=str(uuid.uuid4())[:8],
            trace_id=self._current_session.id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost=cost,
            duration_ms=duration_ms,
            created_at=datetime.now().isoformat(),
            input_messages=json.dumps(input_messages, ensure_ascii=False)[:5000],
            output_message=output_message[:5000] if output_message else "",
        )
        self._current_session.add_llm_call(record)
        return record

    def record_tool(
        self,
        tool_name: str,
        args: dict,
        result: Any,
        duration_ms: int,
        error: Optional[str] = None,
    ) -> Optional[ToolRecord]:
        """记录工具调用"""
        if not self._current_session:
            return None

        # 避免重复序列化：如果 result 已经是字符串，直接使用
        if isinstance(result, str):
            result_str = result[:5000]
        else:
            result_str = json.dumps(result, ensure_ascii=False)[:5000] if result else ""
        error_str = str(error)[:5000] if error else ""

        record = ToolRecord(
            id=str(uuid.uuid4())[:8],
            trace_id=self._current_session.id,
            tool_name=tool_name,
            args=json.dumps(args, ensure_ascii=False)[:2000],
            result=result_str,
            duration_ms=duration_ms,
            created_at=datetime.now().isoformat(),
            error=error_str,
        )
        self._current_session.add_tool_call(record)
        return record

    def flush(self) -> None:
        """批量保存当前会话的所有记录到数据库（事务保护）。"""
        if not self._current_session:
            return
        db_path = _get_db_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("BEGIN")
            if self._current_session.llm_records:
                cursor.executemany(
                    """
                    INSERT INTO llm_calls
                    (id, trace_id, model, input_tokens, output_tokens, total_tokens,
                     cost, duration_ms, created_at, input_messages, output_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    [r.to_tuple() for r in self._current_session.llm_records],
                )
            if self._current_session.tool_records:
                cursor.executemany(
                    """
                    INSERT INTO tool_calls
                    (id, trace_id, tool_name, args, result, duration_ms, created_at, error)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    [r.to_tuple() for r in self._current_session.tool_records],
                )
            cursor.execute("COMMIT")
        except Exception:
            cursor.execute("ROLLBACK")
            raise
        finally:
            conn.close()


def get_tracer() -> Tracer:
    """获取追踪器实例"""
    return Tracer.get_instance()


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """计算 LLM 调用成本 (近似值)"""
    # OpenAI GPT-4o 价格 (每 1M tokens)
    prices = {
        "gpt-4o": (5.0, 15.0),  # input, output per 1M
        "gpt-4o-mini": (0.15, 0.6),
        "gpt-4-turbo": (10.0, 30.0),
        "gpt-3.5-turbo": (0.5, 1.5),
    }

    price = prices.get(model.lower(), (5.0, 15.0))
    input_cost = (input_tokens / 1_000_000) * price[0]
    output_cost = (output_tokens / 1_000_000) * price[1]
    return round(input_cost + output_cost, 6)


# ---- CLI Viewer Functions ----


def list_traces(limit: int = 20) -> list:
    """列出最近的追踪"""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, task, started_at, total_tokens, total_cost, status,
               llm_calls, tool_calls
        FROM traces
        ORDER BY started_at DESC
        LIMIT ?
    """,
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_trace(trace_id: str) -> Optional[dict]:
    """获取追踪详情"""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM traces WHERE id = ?", (trace_id,))
    trace = cursor.fetchone()

    if not trace:
        conn.close()
        return None

    cursor.execute("SELECT * FROM llm_calls WHERE trace_id = ?", (trace_id,))
    llm_calls = cursor.fetchall()

    cursor.execute("SELECT * FROM tool_calls WHERE trace_id = ?", (trace_id,))
    tool_calls = cursor.fetchall()

    conn.close()

    return {
        "trace": trace,
        "llm_calls": llm_calls,
        "tool_calls": tool_calls,
    }


def get_stats() -> dict:
    """获取统计信息"""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*), SUM(total_tokens), SUM(total_cost) FROM traces")
    row = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM llm_calls")
    llm_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tool_calls")
    tool_count = cursor.fetchone()[0]

    conn.close()

    return {
        "total_traces": row[0] or 0,
        "total_tokens": row[1] or 0,
        "total_cost": row[2] or 0.0,
        "total_llm_calls": llm_count,
        "total_tool_calls": tool_count,
    }


def delete_trace(trace_id: str) -> bool:
    """删除追踪"""
    db_path = _get_db_path()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM llm_calls WHERE trace_id = ?", (trace_id,))
        cursor.execute("DELETE FROM tool_calls WHERE trace_id = ?", (trace_id,))
        cursor.execute("DELETE FROM traces WHERE id = ?", (trace_id,))
        deleted = cursor.rowcount > 0
        conn.commit()
    finally:
        conn.close()
    return deleted
