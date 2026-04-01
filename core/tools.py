# core/tools.py  (新增部分)
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional
from loguru import logger
import os

# 安全沙箱目录（所有文件操作都限制在这里）
# 使用绝对路径确保路径解析正确
SANDBOX_DIR = Path(os.path.join(os.getcwd(), "agent_workspace")).resolve()
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

logger.info(f"Sandbox directory initialized: {SANDBOX_DIR}")

class ReadFileInput(BaseModel):
    """读取文件输入"""
    filepath: str = Field(..., description="文件路径（相对于 agent_workspace，例如：'main.py' 或 'src/app.py'，不要包含 'agent_workspace/' 前缀）")

class WriteFileInput(BaseModel):
    """写入文件输入"""
    filepath: str = Field(..., description="文件路径（相对于 agent_workspace，例如：'main.py' 或 'src/app.py'，不要包含 'agent_workspace/' 前缀）")
    content: str = Field(..., description="要写入的内容")
    mode: str = Field(default="w", description="写入模式：w=覆盖, a=追加")

def safe_read_file(filepath: str) -> str:
    """安全读取文件（限制在沙箱目录）"""
    try:
        target = (SANDBOX_DIR / filepath).resolve()
        if not str(target).startswith(str(SANDBOX_DIR)):
            raise ValueError("Access denied: Path outside sandbox")
        if not target.exists():
            return f"File not found: {filepath}"
        content = target.read_text(encoding="utf-8")
        logger.info(f"Read file: {filepath} ({len(content)} chars)")
        return content
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return f"Error: {str(e)}"

def safe_write_file(filepath: str, content: str, mode: str = "w") -> str:
    """安全写入文件（限制在沙箱目录）"""
    try:
        target = (SANDBOX_DIR / filepath).resolve()
        if not str(target).startswith(str(SANDBOX_DIR)):
            raise ValueError("Access denied: Path outside sandbox")
        
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, mode, encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Wrote file: {filepath} ({len(content)} chars)")
        return f"✅ Successfully wrote {len(content)} chars to {filepath}"
    except Exception as e:
        logger.error(f"Error writing file {filepath}: {e}")
        return f"Error: {str(e)}"

# 扩展工具集合 - 可根据需要添加更多工具
class ListDirectoryInput(BaseModel):
    """列出目录输入"""
    path: str = Field(default=".", description="目录路径（相对于 agent_workspace）")

def safe_list_directory(path: str = ".") -> str:
    """安全列出目录内容"""
    try:
        target = (SANDBOX_DIR / path).resolve()
        if not str(target).startswith(str(SANDBOX_DIR)):
            raise ValueError("Access denied: Path outside sandbox")
        
        if not target.exists() or not target.is_dir():
            return f"Directory not found: {path}"
        
        items = []
        for item in target.iterdir():
            item_type = "DIR" if item.is_dir() else "FILE"
            items.append(f"[{item_type}] {item.name}")
        
        result = "\n".join(items) if items else "Directory is empty"
        logger.info(f"Listed directory: {path} ({len(items)} items)")
        return result
    except Exception as e:
        logger.error(f"Error listing directory {path}: {e}")
        return f"Error: {str(e)}"

# 用户交互输入模型
class AskUserQuestionInput(BaseModel):
    """向用户提问输入"""
    question: str = Field(..., description="要向用户提出的问题")
    options: Optional[list[str]] = Field(default=None, description="可选的答案选项（如果有）")

def ask_user_question(question: str, options: Optional[list[str]] = None) -> str:
    """向用户提问并获取回答"""
    try:
        print(f"\n{'='*60}")
        print(f"🤔 Agent 需要你的帮助：")
        print(f"{'='*60}")
        print(f"\n问题：{question}\n")
        
        if options:
            print("可选答案：")
            for i, opt in enumerate(options, 1):
                print(f"  {i}. {opt}")
            print()
        
        print(f"{'='*60}\n")
        
        # 获取用户输入
        answer = input("请输入你的回答：").strip()
        
        # 如果有选项，检查是否输入了选项编号
        if options and answer.isdigit():
            idx = int(answer) - 1
            if 0 <= idx < len(options):
                answer = options[idx]
        
        logger.info(f"User answered: {answer}")
        return answer
    except KeyboardInterrupt:
        logger.warning("User interrupted the question")
        return "用户中断了回答"
    except Exception as e:
        logger.error(f"Error asking user question: {e}")
        return f"Error: {str(e)}"

class PresentDecisionApprovalInput(BaseModel):
    """决策审批输入"""
    analysis: str = Field(..., description="Agent 分析结果（200字内）")
    action: str = Field(..., description="建议行动（100字内）")
    risk: str = Field(default="low", description="风险等级：low/medium/high")

def present_decision_for_approval(
    analysis: str,
    action: str,
    risk: str = "low"
) -> str:
    """向人类展示决策，等待审批（仅用于安全敏感操作）"""
    try:
        # 截断长文本
        analysis_short = analysis[:200] + "..." if len(analysis) > 200 else analysis
        action_short = action[:100] + "..." if len(action) > 100 else action
        
        print(f"\n{'='*50}")
        print(f"⚠️  需要人类审批的决策")
        print(f"{'='*50}")
        print(f"\n分析：{analysis_short}")
        print(f"\n建议：{action_short}")
        print(f"风险：{risk}")
        print(f"{'='*50}\n")
        
        choice = input("批准？: ").strip().lower()
        result = "approved" if choice == 'y' else "rejected"
        
        logger.info(f"Decision {result}: {action_short}")
        return result
    except Exception as e:
        logger.error(f"Error in decision approval: {e}")
        return "error"

# 工具注册辅助函数
def get_tool_registry() -> dict:
    """获取所有可用工具的注册信息"""
    return {
        "read_file": {
            "function": safe_read_file,
            "description": "读取文件内容（限制在 agent_workspace 目录）。路径是相对于 agent_workspace 的，例如：'main.py' 或 'src/app.py'，不要包含 'agent_workspace/' 前缀。",
            "schema": ReadFileInput.model_json_schema()
        },
        "write_file": {
            "function": safe_write_file,
            "description": "写入文件内容（限制在 agent_workspace 目录，支持覆盖和追加模式）。路径是相对于 agent_workspace 的，例如：'main.py' 或 'src/app.py'，不要包含 'agent_workspace/' 前缀。",
            "schema": WriteFileInput.model_json_schema()
        },
        "list_directory": {
            "function": safe_list_directory,
            "description": "列出目录内容（限制在 agent_workspace 目录）。路径是相对于 agent_workspace 的，例如：'.' 或 'src'，不要包含 'agent_workspace/' 前缀。",
            "schema": ListDirectoryInput.model_json_schema()
        },
        "ask_user_question": {
            "function": ask_user_question,
            "description": "向用户提问并获取回答。当 Agent 需要更多上下文信息或用户偏好时使用。可以提供可选答案选项让用户选择。",
            "schema": AskUserQuestionInput.model_json_schema()
        }
    }