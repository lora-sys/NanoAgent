from typing import Any, List, Dict, Optional
from spec.models import PlanStep, AgentPlan

class AgentState:
    """Agent 状态管理 - 支持 Planning + ReAct 循环"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化Agent状态
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self.messages: List[Dict] = []
        self.current_plan: Optional[AgentPlan] = None
        self.step_count: int = 0
        self.observations: List[Dict] = []
        self.reflections: List[Dict] = []
        self.execution_log: List[Dict] = []
        self.completed_steps: List[int] = []
        self.current_context: Dict = {}
        
        # 从配置中读取参数
        core_config = self.config.get("core", {})
        memory_config = core_config.get("memory", {})
        
        self.enable_cache = memory_config.get("enable_cache", True)
        self.max_memory_mb = memory_config.get("max_memory_mb", 1024)
        self.gc_interval = memory_config.get("gc_interval", 100)
        
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
    
    def reset(self) -> None:
        """重置状态"""
        self.messages = []
        self.current_plan = None
        self.step_count = 0
        self.observations = []
        self.reflections = []
        self.execution_log = []
        self.completed_steps = []
        self.current_context = {}
    
    def get_recent_observations(self, limit: int = 5) -> List[Dict]:
        """
        获取最近的观察记录
        
        Args:
            limit: 返回的记录数量
            
        Returns:
            最近的观察记录列表
        """
        return self.observations[-limit:] if self.observations else []
    
    def get_recent_reflections(self, limit: int = 3) -> List[Dict]:
        """
        获取最近的反思记录
        
        Args:
            limit: 返回的记录数量
            
        Returns:
            最近的反思记录列表
        """
        return self.reflections[-limit:] if self.reflections else []
    
    def should_perform_gc(self) -> bool:
        """
        判断是否应该执行垃圾回收
        
        Returns:
            是否应该执行垃圾回收
        """
        return self.step_count > 0 and self.step_count % self.gc_interval == 0
    
    def perform_gc(self) -> None:
        """执行垃圾回收，清理旧的记录"""
        if not self.should_perform_gc():
            return
        
        # 保留最近的消息
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]
        
        # 保留最近的观察记录
        if len(self.observations) > 20:
            self.observations = self.observations[-20:]
        
        # 保留最近的反思记录
        if len(self.reflections) > 10:
            self.reflections = self.reflections[-10:]
        
        logger.info(f"Garbage collection performed at step {self.step_count}")
    
    def get_memory_usage(self) -> Dict[str, int]:
        """
        获取内存使用情况
        
        Returns:
            内存使用统计
        """
        import sys
        return {
            "messages_size": sys.getsizeof(self.messages),
            "observations_size": sys.getsizeof(self.observations),
            "reflections_size": sys.getsizeof(self.reflections),
            "execution_log_size": sys.getsizeof(self.execution_log),
            "total_estimated_mb": (
                sys.getsizeof(self.messages) + 
                sys.getsizeof(self.observations) + 
                sys.getsizeof(self.reflections) + 
                sys.getsizeof(self.execution_log)
            ) / (1024 * 1024)
        }
    
    def is_task_complete(self) -> bool:
        """
        判断任务是否完成
        
        Returns:
            任务是否完成
        """
        if not self.current_plan:
            return False
        
        return len(self.completed_steps) >= len(self.current_plan.steps)
    
    def get_remaining_steps(self) -> List[PlanStep]:
        """
        获取剩余的步骤
        
        Returns:
            剩余步骤列表
        """
        if not self.current_plan:
            return []
        
        return [
            step for step in self.current_plan.steps 
            if step.step_id not in self.completed_steps
        ]
    
    def get_current_step(self) -> Optional[PlanStep]:
        """
        获取当前应该执行的步骤
        
        Returns:
            当前步骤，如果没有则返回None
        """
        remaining = self.get_remaining_steps()
        return remaining[0] if remaining else None
    
    def export_state(self) -> Dict[str, Any]:
        """
        导出完整状态（用于持久化）
        
        Returns:
            完整状态字典
        """
        return {
            "messages": self.messages,
            "current_plan": self.current_plan.model_dump() if self.current_plan else None,
            "step_count": self.step_count,
            "observations": self.observations,
            "reflections": self.reflections,
            "execution_log": self.execution_log,
            "completed_steps": self.completed_steps,
            "current_context": self.current_context,
            "config": self.config,
            "timestamp": self._get_timestamp()
        }
    
    @classmethod
    def import_state(cls, state_data: Dict[str, Any]) -> 'AgentState':
        """
        从导入的状态数据创建AgentState实例
        
        Args:
            state_data: 状态数据字典
            
        Returns:
            AgentState实例
        """
        agent_state = cls(config=state_data.get("config", {}))
        agent_state.messages = state_data.get("messages", [])
        agent_state.step_count = state_data.get("step_count", 0)
        agent_state.observations = state_data.get("observations", [])
        agent_state.reflections = state_data.get("reflections", [])
        agent_state.execution_log = state_data.get("execution_log", [])
        agent_state.completed_steps = state_data.get("completed_steps", [])
        agent_state.current_context = state_data.get("current_context", {})
        
        # 重建current_plan
        plan_data = state_data.get("current_plan")
        if plan_data:
            agent_state.current_plan = AgentPlan(**plan_data)
        
        return agent_state
    
    def __repr__(self) -> str:
        return f"AgentState(step={self.step_count}, observations={len(self.observations)}, plan_steps={len(self.current_plan.steps) if self.current_plan else 0})"