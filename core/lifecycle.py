"""Agent 事件生命周期 — agent > turn > message/tool 三层嵌套"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import auto, Enum
from typing import Any, Callable, Dict, List, Optional


class EventType(Enum):
    """事件类型 — 按嵌套层级排序"""

    AGENT_START = auto()
    AGENT_END = auto()
    TURN_START = auto()
    TURN_END = auto()
    MESSAGE_START = auto()
    MESSAGE_UPDATE = auto()
    MESSAGE_END = auto()
    TOOL_EXECUTION_START = auto()
    TOOL_EXECUTION_UPDATE = auto()
    TOOL_EXECUTION_END = auto()


@dataclass
class TurnContext:
    """Turn 执行上下文"""

    turn_number: int
    iteration: int
    message: Optional[str] = None  # assistant message content
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    start_time: str = field(default_factory=datetime.now)


# ---- 事件 payload dataclasses ----


@dataclass
class AgentStartEvent:
    type: EventType = EventType.AGENT_START
    task: str = ""


@dataclass
class AgentEndEvent:
    type: EventType = EventType.AGENT_END
    status: str = "completed"
    total_turns: int = 0
    total_tools: int = 0


@dataclass
class TurnStartEvent:
    type: EventType = EventType.TURN_START
    turn_context: TurnContext = field(default_factory=TurnContext)


@dataclass
class TurnEndEvent:
    type: EventType = EventType.TURN_END
    turn_context: TurnContext = field(default_factory=TurnContext)


@dataclass
class MessageStartEvent:
    type: EventType = EventType.MESSAGE_START
    turn_number: int = 0


@dataclass
class MessageUpdateEvent:
    type: EventType = EventType.MESSAGE_UPDATE
    turn_number: int = 0
    delta: str = ""


@dataclass
class MessageEndEvent:
    type: EventType = EventType.MESSAGE_END
    turn_number: int = 0
    content: str = ""
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ToolStartEvent:
    type: EventType = EventType.TOOL_EXECUTION_START
    turn_number: int = 0
    tool_call_id: str = ""
    tool_name: str = ""
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolUpdateEvent:
    type: EventType = EventType.TOOL_EXECUTION_UPDATE
    turn_number: int = 0
    tool_call_id: str = ""
    tool_name: str = ""
    partial_result: Any = None


@dataclass
class ToolEndEvent:
    type: EventType = EventType.TOOL_EXECUTION_END
    turn_number: int = 0
    tool_call_id: str = ""
    tool_name: str = ""
    result: Any = None
    is_error: bool = False


# ---- Event payload union type ----

AgentEvent = (
    AgentStartEvent
    | AgentEndEvent
    | TurnStartEvent
    | TurnEndEvent
    | MessageStartEvent
    | MessageUpdateEvent
    | MessageEndEvent
    | ToolStartEvent
    | ToolUpdateEvent
    | ToolEndEvent
)


def event_to_dict(e: AgentEvent) -> Dict[str, Any]:
    """将事件 dataclass 转为 dict"""
    d = {"type": e.type.name}
    for k, v in vars(e).items():
        if k == "type":
            d[k] = v.name
        elif hasattr(v, "__dataclass_fields__"):
            d[k] = vars(v)
        else:
            d[k] = v
    return d


class Lifecycle:
    """
    Agent 执行生命周期管理器。

    规则：
    - agent > turn > message/tool 严格嵌套
    - 通过 _depth 计数器验证嵌套合法性
    """

    # 允许的嵌套层级映射
    _EXPECTED_DEPTH = {
        EventType.AGENT_START: 0,
        EventType.TURN_START: 1,
        EventType.MESSAGE_START: 2,
        EventType.TOOL_EXECUTION_START: 2,
        EventType.MESSAGE_UPDATE: 3,
        EventType.TOOL_EXECUTION_UPDATE: 3,
        EventType.MESSAGE_END: 3,
        EventType.TOOL_EXECUTION_END: 3,
        EventType.TURN_END: 1,
        EventType.AGENT_END: 0,
    }

    def __init__(self):
        self._handlers: List[Callable[[AgentEvent], None]] = []
        self._depth = 0
        self._total_turns = 0
        self._total_tools = 0
        self._turn_number = 0

    def subscribe(self, handler: Callable[[AgentEvent], None]) -> None:
        """注册事件处理器。"""
        self._handlers.append(handler)

    def unsubscribe(self, handler: Callable[[AgentEvent], None]) -> None:
        """注销事件处理器。"""
        self._handlers.remove(handler)

    def emit(self, event: AgentEvent) -> None:
        """分发事件到所有 handler。"""
        expected = self._EXPECTED_DEPTH.get(event.type)
        if expected is not None and expected != self._depth:
            raise RuntimeError(
                f"Event {event.type.name} emitted at depth {self._depth}, "
                f"expected {expected}"
            )

        # 更新嵌套深度
        if event.type in (
            EventType.AGENT_START,
            EventType.TURN_START,
            EventType.MESSAGE_START,
            EventType.TOOL_EXECUTION_START,
        ):
            self._depth += 1
        elif event.type in (
            EventType.AGENT_END,
            EventType.TURN_END,
            EventType.MESSAGE_END,
            EventType.TOOL_EXECUTION_END,
        ):
            self._depth -= 1

        # 统计
        if event.type == EventType.TURN_START:
            self._total_turns += 1
            self._turn_number += 1
        if event.type == EventType.TOOL_EXECUTION_END:
            self._total_tools += 1

        # 分发
        for handler in self._handlers:
            handler(event)

    def get_turn_number(self) -> int:
        return self._turn_number

    def get_totals(self) -> tuple[int, int]:
        return self._total_turns, self._total_tools

