"""Execution result dataclasses."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorStrategy(Enum):
    """Error handling strategy."""

    STOP = "stop"  # Stop all tasks on any failure
    FAIL_FAST = "fail-fast"  # Cancel remaining on first failure
    CONTINUE = "continue"  # Ignore failures, continue execution


class ExecutionStrategy(Enum):
    """Execution mode."""

    PARALLEL = "parallel"
    SERIAL = "serial"
    CONDITIONAL = "conditional"


@dataclass
class ExecutionResult:
    """Result of a single task execution."""

    node_id: str
    output: Any = None
    error: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    duration: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "output": self.output,
            "error": self.error,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration": self.duration,
        }


@dataclass
class ExecutionStatus:
    """Overall execution state."""

    results: Dict[str, ExecutionResult] = field(default_factory=dict)
    strategy: ExecutionStrategy = ExecutionStrategy.PARALLEL
    error_strategy: ErrorStrategy = ErrorStrategy.STOP
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    total_duration: Optional[float] = None

    def add_result(self, result: ExecutionResult) -> None:
        self.results[result.node_id] = result

    def get_result(self, node_id: str) -> Optional[ExecutionResult]:
        return self.results.get(node_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "results": {k: v.to_dict() for k, v in self.results.items()},
            "strategy": self.strategy.value,
            "error_strategy": self.error_strategy.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration": self.total_duration,
        }
