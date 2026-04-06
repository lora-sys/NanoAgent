"""人类反馈用于学习工具（RLHF）"""
from pydantic import BaseModel, Field
from loguru import logger
from typing import Optional
from enum import Enum
import hashlib
import json
from datetime import datetime
from cli_interface import get_cli

class FeedbackType(str, Enum):
    """反馈类型"""
    CORRECTNESS = "correctness"  # 正确性反馈
    QUALITY = "quality"         # 质量反馈
    CLARITY = "clarity"         # 清晰度反馈
    SAFETY = "safety"           # 安全性反馈
    GENERAL = "general"         # 一般反馈

class CollectFeedbackInput(BaseModel):
    """收集反馈输入"""
    feedback_type: FeedbackType = Field(..., description="反馈类型：correctness/quality/clarity/safety/general")
    step_id: str = Field(..., description="相关步骤ID")
    content: str = Field(..., description="Agent 生成的内容")
    question: Optional[str] = Field(default=None, description="引导性问题（可选）")

def collect_human_feedback(
    feedback_type: str,
    step_id: str,
    content: str,
    question: Optional[str] = None
) -> str:
    """
    收集人类反馈（用于模型学习）
    
    典型应用：
    - RLHF（人类反馈强化学习）
    - 收集人类偏好
    - 优化 AI 模型
    
    反馈将影响智能体的学习轨迹
    """
    try:
        cli = get_cli()
        feedback = cli.display_feedback(feedback_type, step_id, content, question)
        
        # 记录反馈数据
        feedback_record = {
            "timestamp": datetime.now().isoformat(),
            "feedback_type": feedback_type,
            "step_id": step_id,
            "feedback": feedback,
            "content_preview": content[:100] + "..." if len(content) > 100 else content
        }
        
        logger.info(f"Human feedback collected: {json.dumps(feedback_record, ensure_ascii=False)}")
        return feedback
        
    except ValueError:
        logger.error(f"Invalid feedback type: {feedback_type}")
        return f"Error: Invalid type '{feedback_type}'"
    except Exception as e:
        logger.error(f"Error collecting feedback: {e}")
        return f"Error: {str(e)}"