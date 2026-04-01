from typing import Any, List, Dict, Optional
from pydantic import BaseModel

class PlanStep(BaseModel):
    """计划步骤"""
    step_id: int
    goal: str
    suggested_tools: List[str] = []
    depends_on: List[int] = []
    success_criteria: str = ""
    risk_assessment: str = ""

class AgentPlan(BaseModel):
    """执行计划"""
    steps: List[PlanStep] = []
    overall_goal: str = ""
    estimated_steps: int = 0
    critical_path: List[int] = []

class AgentState:
    """Agent 状态管理 - 支持 Planning + ReAct 循环"""
    
    def __init__(self):
        self.messages: List[Dict] = []
        self.current_plan: Optional[AgentPlan] = None
        self.step_count: int = 0
        self.observations: List[Dict] = []
        self.reflections: List[Dict] = []
        self.execution_log: List[Dict] = []
        self.completed_steps: List[int] = []
        self.current_context: Dict = {}
        
    def add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": self._get_timestamp()
        })
    
    def add_observation(self, step: int, action: Dict, result: Any, analysis: str = ""):
        """添加观察记录"""
        observation = {
            "step": step,
            "action": action,
            "result": str(result)[:500],
            "analysis": analysis[:500],
            "timestamp": self._get_timestamp()
        }
        self.observations.append(observation)
        self._log_execution("observation", observation)
    
    def add_reflection(self, reflection: Dict):
        """添加反思记录"""
        reflection_record = {
            "step": self.step_count,
            "reflection": reflection,
            "timestamp": self._get_timestamp()
        }
        self.reflections.append(reflection_record)
        self._log_execution("reflection", reflection_record)
    
    def mark_step_completed(self, step_id: int):
        """标记步骤为已完成"""
        if step_id not in self.completed_steps:
            self.completed_steps.append(step_id)
    
    def update_context(self, key: str, value: Any):
        """更新上下文信息"""
        self.current_context[key] = value
    
    def get_progress(self) -> Dict:
        """获取当前进度"""
        total_steps = len(self.current_plan.steps) if self.current_plan else 0
        completed = len(self.completed_steps)
        return {
            "total_steps": total_steps,
            "completed_steps": completed,
            "progress_percentage": (completed / total_steps * 100) if total_steps > 0 else 0,
            "current_step": self.step_count,
            "observations_count": len(self.observations),
            "reflections_count": len(self.reflections)
        }
    
    def get_execution_summary(self) -> str:
        """获取执行摘要"""
        progress = self.get_progress()
        return (
            f"执行摘要:\n"
            f"  - 总步骤: {progress['total_steps']}\n"
            f"  - 已完成: {progress['completed_steps']}\n"
            f"  - 进度: {progress['progress_percentage']:.1f}%\n"
            f"  - 当前步骤: {progress['current_step']}\n"
            f"  - 观察记录: {progress['observations_count']}\n"
            f"  - 反思次数: {progress['reflections_count']}"
        )
    
    def _log_execution(self, event_type: str, data: Dict):
        """记录执行日志"""
        self.execution_log.append({
            "event_type": event_type,
            "data": data,
            "timestamp": self._get_timestamp()
        })
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "messages": self.messages,
            "current_plan": self.current_plan.model_dump() if self.current_plan else None,
            "step_count": self.step_count,
            "observations": self.observations,
            "reflections": self.reflections,
            "completed_steps": self.completed_steps,
            "current_context": self.current_context,
            "progress": self.get_progress()
        }
    
    def summary(self) -> str:
        """获取简短摘要"""
        return self.get_execution_summary()