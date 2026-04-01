"""人机交互工具 (HITL - Human in the Loop)"""
from .ask import AskUserQuestionInput, ask_user_question
from .approve import PresentDecisionApprovalInput, present_decision_for_approval
from .monitor import MonitorInput, monitor_agent
from .intervene import InterveneInput, human_intervention
from .feedback import CollectFeedbackInput, collect_human_feedback
from .escalate import EscalateInput, escalate_to_human

__all__ = [
    # 基础交互
    'AskUserQuestionInput',
    'ask_user_question',
    'PresentDecisionApprovalInput',
    'present_decision_for_approval',
    # 人类监督
    'MonitorInput',
    'monitor_agent',
    # 干预与纠正
    'InterveneInput',
    'human_intervention',
    # 人类反馈
    'CollectFeedbackInput',
    'collect_human_feedback',
    # 升级策略
    'EscalateInput',
    'escalate_to_human'
]