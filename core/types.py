"""
类型定义模块

消除 Any 使用，提供具体类型定义和 Protocol。
包含 Agent 执行过程中的各种数据结构和协议。
"""

from typing import Dict, Any, Optional, List, Union, Protocol, TypeVar
from pydantic import BaseModel


# ============ 通用类型 ============

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONObject = Dict[str, JSONValue]
JSONArray = List[JSONValue]


# ============ Agent 相关类型 ============


class AgentState(BaseModel):
    """Agent 状态模型。

    Attributes:
        current_state: 当前状态字符串。
        previous_state: 前一个状态。
        metadata: 附加元数据。
        updated_at: 更新时间戳。
    """

    current_state: str
    previous_state: Optional[str] = None
    metadata: Dict[str, Any] = {}
    updated_at: Optional[str] = None


class ObservationRecord(BaseModel):
    """观察记录模型。

    Attributes:
        step: 步骤编号。
        action: 执行的动作。
        result: 执行结果。
        timestamp: 记录时间。
        metadata: 附加元数据。
    """

    step: int
    action: str
    result: str
    timestamp: str
    metadata: Dict[str, Any] = {}


class DecisionRecord(BaseModel):
    """决策记录模型。

    Attributes:
        decision: 决策内容。
        reason: 决策原因。
        timestamp: 记录时间。
        metadata: 附加元数据。
    """

    decision: str
    reason: str
    timestamp: str
    metadata: Dict[str, Any] = {}


class ArtifactRecord(BaseModel):
    """交付物记录模型。

    Attributes:
        name: 交付物名称。
        type: 交付物类型。
        path: 文件路径。
        created_at: 创建时间。
        metadata: 附加元数据。
    """

    name: str
    type: str
    path: str
    created_at: str
    metadata: Dict[str, Any] = {}


class ExecutionContext(BaseModel):
    """执行上下文模型。

    Attributes:
        task: 任务描述。
        spec: 任务规范。
        current_stage: 当前阶段。
        constraints: 约束条件。
        observations: 观察记录列表。
        decisions: 决策记录列表。
        artifacts: 交付物记录列表。
    """

    task: str
    spec: Optional[str] = None
    current_stage: Optional[str] = None
    constraints: Dict[str, Any] = {}
    observations: List[ObservationRecord] = []
    decisions: List[DecisionRecord] = []
    artifacts: List[ArtifactRecord] = []


class ExecutionResult(BaseModel):
    """执行结果模型。

    Attributes:
        success: 是否成功。
        task: 任务描述。
        duration: 执行耗时（秒）。
        observations_count: 观察记录数。
        decisions_count: 决策记录数。
        artifacts_count: 交付物数量。
        error: 错误信息（如果有）。
    """

    success: bool
    task: str
    duration: Optional[float] = None
    observations_count: int = 0
    decisions_count: int = 0
    artifacts_count: int = 0
    error: Optional[str] = None


# ============ LLM 相关类型 ============


class LLMMessage(BaseModel):
    """LLM 消息模型。

    Attributes:
        role: 消息角色（user/system/assistant）。
        content: 消息内容。
    """

    role: str
    content: str


class LLMToolCall(BaseModel):
    """LLM 工具调用模型。

    Attributes:
        id: 调用 ID。
        name: 工具名称。
        arguments: 调用参数。
    """

    id: str
    name: str
    arguments: Dict[str, Any]


class LLMResponse(BaseModel):
    """LLM 响应模型。

    Attributes:
        content: 响应内容。
        tool_calls: 工具调用列表。
        usage: Token 使用统计。
    """

    content: str
    tool_calls: Optional[List[LLMToolCall]] = None
    usage: Optional[Dict[str, int]] = None


# ============ 工具相关类型 ============


class ToolSchema(BaseModel):
    """工具 Schema 模型。

    Attributes:
        name: 工具名称。
        description: 工具描述。
        parameters: 参数定义。
    """

    name: str
    description: str
    parameters: Dict[str, Any]


class ToolResult(BaseModel):
    """工具执行结果模型。

    Attributes:
        success: 是否成功。
        output: 输出内容。
        error: 错误信息。
    """

    success: bool
    output: str
    error: Optional[str] = None


# ============ 配置相关类型 ============


class ConfigValue(BaseModel):
    """配置值模型。

    Attributes:
        value: 配置值。
        source: 配置来源。
        updated_at: 更新时间。
    """

    value: Any
    source: Optional[str] = None
    updated_at: Optional[str] = None


# ============ 协议定义（替代 Any） ============


class StateManagerProtocol(Protocol):
    """状态管理器协议。

    定义了状态管理器必须实现的方法接口。
    """

    def get_current_state(self) -> str: ...
    def is_requirements_confirmed(self) -> bool: ...
    def get_requirements_summary(self) -> str: ...
    def add_observation(self, step: int, action: str, result: str) -> None: ...
    def add_requirement(self, requirement: str) -> None: ...


class PersistenceManagerProtocol(Protocol):
    """持久化管理器协议。

    定义了持久化操作必须实现的方法接口。
    """

    def read_json(self, path: str) -> Optional[JSONObject]: ...
    def write_json(self, path: str, data: JSONObject) -> None: ...
    def read_text(self, path: str) -> Optional[str]: ...
    def write_text(self, path: str, content: str) -> None: ...


class CacheManagerProtocol(Protocol):
    """缓存管理器协议。

    定义了缓存操作必须实现的方法接口。
    """

    def get(self, key: str) -> Optional[Any]: ...
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def clear(self) -> None: ...
