"""简单的任务跟踪系统"""

from typing import Any, Dict, List
from datetime import datetime
import json
from pathlib import Path


class TaskSpec:
    """轻量级任务规范跟踪器"""

    def __init__(self, task: str):
        self.task = task
        self.created_at = datetime.now().isoformat()
        self.status = "running"
        self.steps_executed = 0
        self.tools_used: List[str] = []
        self.artifacts: List[str] = []
        self.decisions: List[str] = []
        self.errors: List[str] = []

    def add_tool_call(self, tool_name: str):
        """记录工具调用"""
        if tool_name not in self.tools_used:
            self.tools_used.append(tool_name)
        self.steps_executed += 1

    def add_artifact(self, artifact: str):
        """记录生成的文件/产物"""
        if artifact not in self.artifacts:
            self.artifacts.append(artifact)

    def add_decision(self, decision: str):
        """记录重要决策"""
        if decision not in self.decisions:
            self.decisions.append(decision)

    def add_error(self, error: str):
        """记录错误"""
        self.errors.append(error)

    def complete(self):
        """标记任务完成"""
        self.status = "completed"

    def fail(self, reason: str):
        """标记任务失败"""
        self.status = "failed"
        self.add_error(reason)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task": self.task,
            "created_at": self.created_at,
            "status": self.status,
            "steps_executed": self.steps_executed,
            "tools_used": self.tools_used,
            "artifacts": self.artifacts,
            "decisions": self.decisions,
            "errors": self.errors,
        }

    def save(self, filepath: str = None):
        """保存到文件"""
        if filepath is None:
            # 使用微秒级时间戳避免命名冲突
            filepath = f".spec/{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        return filepath
