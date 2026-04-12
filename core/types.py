"""Core type definitions and protocols."""

from typing import Dict, Any, Optional, List, Union, Protocol, TypeVar
from pydantic import BaseModel

T = TypeVar("T")
JSONValue = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONObject = Dict[str, JSONValue]


class AgentState(BaseModel):
    current_state: str
    previous_state: Optional[str] = None
    metadata: Dict[str, Any] = {}
    updated_at: Optional[str] = None


class ObservationRecord(BaseModel):
    step: int
    action: str
    result: str
    timestamp: str
    metadata: Dict[str, Any] = {}


class DecisionRecord(BaseModel):
    decision: str
    reason: str
    timestamp: str
    metadata: Dict[str, Any] = {}


class ArtifactRecord(BaseModel):
    name: str
    type: str
    path: str
    created_at: str
    metadata: Dict[str, Any] = {}


class ExecutionContext(BaseModel):
    task: str
    spec: Optional[str] = None
    current_stage: Optional[str] = None
    constraints: Dict[str, Any] = {}
    observations: List[ObservationRecord] = []
    decisions: List[DecisionRecord] = []
    artifacts: List[ArtifactRecord] = []


class ExecutionResult(BaseModel):
    success: bool
    task: str
    duration: Optional[float] = None
    observations_count: int = 0
    decisions_count: int = 0
    artifacts_count: int = 0
    error: Optional[str] = None


class LLMMessage(BaseModel):
    role: str
    content: str


class LLMToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


class LLMResponse(BaseModel):
    content: str
    tool_calls: Optional[List[LLMToolCall]] = None
    usage: Optional[Dict[str, int]] = None


class ToolSchema(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]


class ToolResult(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None


class ConfigValue(BaseModel):
    value: Any
    source: Optional[str] = None
    updated_at: Optional[str] = None


class StateManagerProtocol(Protocol):
    def get_current_state(self) -> str: ...
    def is_requirements_confirmed(self) -> bool: ...
    def get_requirements_summary(self) -> str: ...
    def add_observation(self, step: int, action: str, result: str) -> None: ...
    def add_requirement(self, requirement: str) -> None: ...


class PersistenceManagerProtocol(Protocol):
    def read_json(self, path: str) -> Optional[JSONObject]: ...
    def write_json(self, path: str, data: JSONObject) -> None: ...
    def read_text(self, path: str) -> Optional[str]: ...
    def write_text(self, path: str, content: str) -> None: ...


class CacheManagerProtocol(Protocol):
    def get(self, key: str) -> Optional[Any]: ...
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None: ...
    def delete(self, key: str) -> None: ...
    def clear(self) -> None: ...
