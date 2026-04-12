from typing import Any, List, Dict, Optional
from spec.models import PlanStep, AgentPlan
from loguru import logger
from domain.entities.state_machine import StateMachine, AgentState as StateMachineState


class AgentState:
    """Agent 状态管理 - 支持 Planning + ReAct 循环 + 状态机"""

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

        # 需求信息集中存储
        self.requirements: Dict[str, Any] = {}  # 存储需求信息
        self.requirements_confirmed: bool = False  # 需求确认标记
        self.requirements_history: List[Dict] = []  # 需求收集历史记录

        # 决策和交付物管理
        self.decisions: List[Dict] = []  # 存储决策记录
        self.artifacts: List[Dict] = []  # 存储交付物记录

        # 新增：状态机
        self.state_machine = StateMachine()

        # 从配置中读取参数（支持完整config或core_config）
        if config and "core" in config:
            # 传入的是完整配置
            core_config = config.get("core", {})
        else:
            # 传入的是core_config本身
            core_config = config or {}

        memory_config = core_config.get("memory", {})

        self.enable_cache = memory_config.get("enable_cache", True)
        self.max_memory_mb = memory_config.get("max_memory_mb", 1024)
        self.gc_interval = memory_config.get("gc_interval", 100)

    def add_message(self, role: str, content: str):
        """添加消息到对话历史"""
        self.messages.append(
            {"role": role, "content": content, "timestamp": self._get_timestamp()}
        )

    def add_observation(self, step: int, action: Dict, result: Any, analysis: str = ""):
        """添加观察记录。

        如果观察到的行动是成功的文件写入操作，自动将文件记录为交付物。
        """
        observation = {
            "step": step,
            "action": action,
            "result": str(result)[:500],
            "analysis": analysis[:500],
            "timestamp": self._get_timestamp(),
        }
        self.observations.append(observation)
        self._log_execution("observation", observation)

        # 自动提取交付物：检查是否是成功的文件写入操作
        self._auto_extract_artifact(action, result)

    def add_reflection(self, reflection: Dict):
        """添加反思记录"""
        reflection_record = {
            "step": self.step_count,
            "reflection": reflection,
            "timestamp": self._get_timestamp(),
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

    def save_requirement(self, key: str, value: Any, category: str = "general"):
        """
        保存需求信息

        Args:
            key: 需求键名
            value: 需求值
            category: 需求分类（如：modules, style, tech_scope 等）
        """
        self.requirements[key] = {
            "value": value,
            "category": category,
            "timestamp": self._get_timestamp(),
        }

        # 记录到历史
        self.requirements_history.append(
            {
                "key": key,
                "value": value,
                "category": category,
                "timestamp": self._get_timestamp(),
            }
        )

        logger.info(f"Requirement saved: {key} = {value[:100]}...")

    def get_requirement(self, key: str) -> Optional[Any]:
        """
        获取需求信息

        Args:
            key: 需求键名

        Returns:
            需求值，如果不存在则返回 None
        """
        req = self.requirements.get(key)
        return req["value"] if req else None

    def get_requirements_summary(self) -> str:
        """
        获取需求信息摘要

        Returns:
            需求信息摘要字符串
        """
        if not self.requirements:
            return "暂无需求信息"

        summary_lines = ["已收集的需求信息："]

        # 按分类组织
        categories = {}
        for key, req_data in self.requirements.items():
            category = req_data.get("category", "general")
            if category not in categories:
                categories[category] = []
            categories[category].append((key, req_data["value"]))

        # 生成摘要
        for category, items in categories.items():
            summary_lines.append(f"\n【{category}】")
            for key, value in items:
                value_str = str(value)[:150]
                summary_lines.append(f"  - {key}: {value_str}")

        # 添加确认状态
        if self.requirements_confirmed:
            summary_lines.append("\n✅ 需求已确认")
        else:
            summary_lines.append("\n⏳ 需求待确认")

        # 添加当前状态
        current_state = self.get_current_state()
        summary_lines.append(f"\n🔄 当前状态: {current_state.value}")

        return "\n".join(summary_lines)

    def confirm_requirements(self):
        """标记需求已确认（触发状态转换）"""
        self.requirements_confirmed = True
        logger.info("Requirements confirmed, triggering state transition")

        # 触发状态转换（只有在 REQUIREMENT_GATHERING 状态时才转换）
        try:
            current_state = self.state_machine.get_current_state()
            if current_state == StateMachineState.REQUIREMENT_GATHERING:
                self.state_machine.transition(
                    StateMachineState.REQUIREMENT_CONFIRMED,
                    "用户确认需求",
                    {"step_count": self.step_count},
                )
            else:
                logger.warning(
                    f"Cannot transition to REQUIREMENT_CONFIRMED from {current_state.value}, "
                    "expected REQUIREMENT_GATHERING"
                )
        except ValueError as e:
            logger.error(f"State transition failed: {e}")

    def is_requirements_confirmed(self) -> bool:
        """
        检查需求是否已确认

        Returns:
            需求是否已确认
        """
        return self.requirements_confirmed

    def get_current_state(self) -> StateMachineState:
        """
        获取当前状态

        Returns:
            当前状态
        """
        return self.state_machine.get_current_state()

    def get_transition_history(self) -> List[Dict]:
        """
        获取状态转换历史

        Returns:
            状态转换历史列表
        """
        return self.state_machine.get_transition_history()

    def get_requirements_by_category(self, category: str) -> Dict[str, Any]:
        """
        按分类获取需求信息

        Args:
            category: 需求分类

        Returns:
            该分类下的所有需求
        """
        result = {}
        for key, req_data in self.requirements.items():
            if req_data.get("category") == category:
                result[key] = req_data["value"]
        return result

    # ========== 决策管理方法 ==========

    def add_decision(self, decision: str, rationale: str = "", step: int = None):
        """
        添加决策记录

        Args:
            decision: 决策内容
            rationale: 决策理由
            step: 决策所在的步骤
        """
        self.decisions.append(
            {
                "decision": decision,
                "rationale": rationale,
                "step": step if step is not None else self.step_count,
                "timestamp": self._get_timestamp(),
            }
        )
        logger.info(f"Decision added: {decision[:100]}...")

    def get_decisions(self) -> List[Dict]:
        """
        获取所有决策

        Returns:
            决策列表，格式为 [{"decision": "...", "rationale": ""}]
        """
        formatted_decisions = []
        for d in self.decisions:
            if isinstance(d, dict):
                # 已经是正确格式
                formatted_decisions.append(d)
            elif isinstance(d, str):
                # 将字符串决策转换为字典格式
                formatted_decisions.append(
                    {"decision": d, "rationale": "从执行记录中提取"}
                )

        return formatted_decisions

    def get_decisions_summary(self) -> str:
        """
        获取决策摘要

        Returns:
            决策摘要字符串
        """
        if not self.decisions:
            return "暂无决策记录"

        summary_lines = [f"已记录 {len(self.decisions)} 个决策：\n"]
        for i, decision in enumerate(self.decisions, 1):
            summary_lines.append(f"{i}. {decision['decision']}")
            if decision.get("rationale"):
                summary_lines.append(f"   理由: {decision['rationale'][:100]}...")

        return "\n".join(summary_lines)

    def clear_decisions(self):
        """清空决策记录（通常在阶段推进后调用）"""
        self.decisions = []
        logger.info("Decisions cleared")

    # ========== 交付物管理方法 ==========

    def add_artifact(self, artifact_path: str, description: str = "", step: int = None):
        """
        添加交付物记录（可能触发状态转换）

        Args:
            artifact_path: 交付物路径
            description: 交付物描述
            step: 创建交付物的步骤
        """
        self.artifacts.append(
            {
                "path": artifact_path,
                "description": description,
                "step": step if step is not None else self.step_count,
                "timestamp": self._get_timestamp(),
            }
        )
        logger.info(f"Artifact added: {artifact_path}")

        # 根据当前状态进行合适的状态转换
        try:
            current_state = self.state_machine.get_current_state()

            if current_state == StateMachineState.REQUIREMENT_CONFIRMED:
                # 从需求确认状态转换到规划状态
                self.state_machine.transition(
                    StateMachineState.PLANNING,
                    "创建第一个交付物，开始规划",
                    {"artifact_path": artifact_path},
                )
                logger.info("State transition: REQUIREMENT_CONFIRMED -> PLANNING")
            elif current_state == StateMachineState.PLANNING:
                # 从规划状态转换到执行状态
                self.state_machine.transition(
                    StateMachineState.EXECUTING,
                    "开始执行任务",
                    {"artifact_path": artifact_path},
                )
                logger.info("State transition: PLANNING -> EXECUTING")
            elif current_state == StateMachineState.EXECUTING:
                # 已经在执行状态，不需要转换
                logger.debug("Already in EXECUTING state, no transition needed")
            else:
                # 其他状态（INITIAL, REQUIREMENT_GATHERING 等）不进行状态转换
                logger.debug(
                    f"Current state {current_state.value}, not transitioning on artifact creation"
                )
        except ValueError as e:
            # 状态转换失败，记录错误但不影响交付物添加
            logger.warning(f"State transition failed: {e}, artifact still added")

    def _auto_extract_artifact(self, action: Dict, result: Any):
        """自动从文件写入操作中提取交付物。

        当工具执行结果为成功的文件写入时，自动将文件路径添加为交付物。

        Args:
            action: 执行的行动字典。
            result: 执行结果。
        """
        if not isinstance(action, dict):
            return

        tool = action.get("tool", "")
        arguments = action.get("arguments", {})
        filepath = arguments.get("filepath", "")

        # 检查是否是文件写入操作
        if tool in ("safe_write_file", "write_file") and filepath:
            # 检查结果是否成功
            result_str = str(result)
            if "Successfully wrote" in result_str or "wrote" in result_str.lower():
                # 检查该文件是否已经被记录过
                existing_paths = [a.get("path", "") for a in self.artifacts]
                if filepath not in existing_paths:
                    # 自动添加为交付物
                    self.add_artifact(
                        artifact_path=filepath,
                        description="自动检测到的项目文件",
                        step=self.step_count,
                    )

    def get_artifacts(self) -> List[str]:
        """
        获取所有交付物路径

        Returns:
            交付物路径列表
        """
        return [a["path"] for a in self.artifacts]

    def get_artifacts_summary(self) -> str:
        """
        获取交付物摘要

        Returns:
            交付物摘要字符串
        """
        if not self.artifacts:
            return "暂无交付物记录"

        summary_lines = [f"已创建 {len(self.artifacts)} 个交付物：\n"]
        for i, artifact in enumerate(self.artifacts, 1):
            summary_lines.append(f"{i}. {artifact['path']}")
            if artifact.get("description"):
                summary_lines.append(f"   描述: {artifact['description'][:100]}...")

        return "\n".join(summary_lines)

    def clear_artifacts(self):
        """清空交付物记录（通常在阶段推进后调用）"""
        self.artifacts = []
        logger.info("Artifacts cleared")

    def get_progress(self) -> Dict:
        """获取当前进度"""
        total_steps = len(self.current_plan.steps) if self.current_plan else 0
        completed = len(self.completed_steps)
        return {
            "total_steps": total_steps,
            "completed_steps": completed,
            "progress_percentage": (completed / total_steps * 100)
            if total_steps > 0
            else 0,
            "current_step": self.step_count,
            "observations_count": len(self.observations),
            "reflections_count": len(self.reflections),
            "decisions_count": len(self.decisions),
            "artifacts_count": len(self.artifacts),
            "current_state": self.get_current_state().value,
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
            f"  - 反思次数: {progress['reflections_count']}\n"
            f"  - 决策数量: {progress['decisions_count']}\n"
            f"  - 交付物数量: {progress['artifacts_count']}\n"
            f"  - 当前状态: {progress['current_state']}"
        )

    def _log_execution(self, event_type: str, data: Dict):
        """记录执行日志"""
        self.execution_log.append(
            {"event_type": event_type, "data": data, "timestamp": self._get_timestamp()}
        )

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "messages": self.messages,
            "current_plan": self.current_plan.model_dump()
            if self.current_plan
            else None,
            "step_count": self.step_count,
            "observations": self.observations,
            "reflections": self.reflections,
            "completed_steps": self.completed_steps,
            "current_context": self.current_context,
            "progress": self.get_progress(),
            "decisions": self.decisions,
            "artifacts": self.artifacts,
            "current_state": self.get_current_state().value,
            "transition_history": self.get_transition_history(),
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
        self.requirements = {}
        self.requirements_confirmed = False
        self.requirements_history = []
        self.decisions = []
        self.artifacts = []
        self.state_machine = StateMachine()

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
                sys.getsizeof(self.messages)
                + sys.getsizeof(self.observations)
                + sys.getsizeof(self.reflections)
                + sys.getsizeof(self.execution_log)
            )
            / (1024 * 1024),
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
            step
            for step in self.current_plan.steps
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
            "current_plan": self.current_plan.model_dump()
            if self.current_plan
            else None,
            "step_count": self.step_count,
            "observations": self.observations,
            "reflections": self.reflections,
            "execution_log": self.execution_log,
            "completed_steps": self.completed_steps,
            "current_context": self.current_context,
            "config": self.config,
            "timestamp": self._get_timestamp(),
            "decisions": self.decisions,
            "artifacts": self.artifacts,
            "current_state": self.get_current_state().value,
            "transition_history": self.get_transition_history(),
        }

    @classmethod
    def import_state(cls, state_data: Dict[str, Any]) -> "AgentState":
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
        agent_state.decisions = state_data.get("decisions", [])
        agent_state.artifacts = state_data.get("artifacts", [])

        # 重建current_plan
        plan_data = state_data.get("current_plan")
        if plan_data:
            agent_state.current_plan = AgentPlan(**plan_data)

        return agent_state

    def __repr__(self) -> str:
        return f"AgentState(step={self.step_count}, observations={len(self.observations)}, plan_steps={len(self.current_plan.steps) if self.current_plan else 0}, state={self.get_current_state().value})"
