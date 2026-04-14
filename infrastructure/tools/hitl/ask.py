"""向用户提问工具"""

from pydantic import BaseModel, Field
from loguru import logger
from typing import Optional
import sys
from presentation.cli.interface import get_cli


class AskUserQuestionInput(BaseModel):
    """向用户提问输入"""
    question: str = Field(..., description="要向用户提出的问题")
    options: Optional[list[str]] = Field(default=None, description="可选答案")


def ask_user_question(question: str, options: Optional[list[str]] = None) -> str:
    """向用户提问并获取回答"""
    try:
        if not sys.stdin.isatty():
            # 非交互模式（测试/管道），返回默认答案
            logger.info(f"非交互模式，跳过用户提问: {question}")
            return "继续执行"
        cli = get_cli()
        answer = cli.display_question(question, options)
        logger.info(f"User answered: {answer}")
        return answer
    except Exception as e:
        logger.error(f"Error asking user question: {e}")
        return f"Error: {str(e)}"
