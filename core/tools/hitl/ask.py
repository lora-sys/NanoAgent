"""向用户提问工具"""
from pydantic import BaseModel, Field
from loguru import logger
from typing import Optional
from cli_interface import get_cli

class AskUserQuestionInput(BaseModel):
    """向用户提问输入"""
    question: str = Field(..., description="要向用户提出的问题")
    options: Optional[list[str]] = Field(default=None, description="可选的答案选项（如果有）")

def ask_user_question(question: str, options: Optional[list[str]] = None) -> str:
    """向用户提问并获取回答（用于需要用户偏好或澄清的场景）"""
    try:
        cli = get_cli()
        answer = cli.display_question(question, options)
        logger.info(f"User answered: {answer}")
        return answer
    except Exception as e:
        logger.error(f"Error asking user question: {e}")
        return f"Error: {str(e)}"