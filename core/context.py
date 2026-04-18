"""共享上下文基类"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class ExecutionContext:
    """执行上下文基类 - ChainContext 和 RouteContext 的共享实现"""

    data: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        """设置上下文数据"""
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.data.get(key, default)

    def add_history(self, **kwargs) -> None:
        """添加执行历史 - 子类实现具体的记录格式"""
        self.history.append({**kwargs, "timestamp": datetime.now().isoformat()})

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {"data": self.data, "history": self.history, "metadata": self.metadata}


class ChainContext(ExecutionContext):
    """链式执行上下文"""

    def add_history(self, step_name: str, result: Any) -> None:
        super().add_history(step=step_name, result=result)


class RouteContext(ExecutionContext):
    """路由上下文"""

    def add_history(self, decision: Any, task: str) -> None:
        super().add_history(
            task=task,
            decision=decision.to_dict() if hasattr(decision, "to_dict") else decision,
        )
