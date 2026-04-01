"""人类监督工具（日志审查、实时监控）"""
from pydantic import BaseModel, Field
from loguru import logger
from typing import Optional
import json
from datetime import datetime
import sys
sys.path.insert(0, "/home/lora/repos/nanoagent")
from cli_interface import get_cli

class MonitorInput(BaseModel):
    """监督输入"""
    action: str = Field(..., description="需要监督的动作类型：log_review/realtime_check")
    step_id: str = Field(..., description="当前步骤ID")
    output: str = Field(..., description="Agent 输出内容")
    context: Optional[str] = Field(default=None, description="额外上下文信息")

def monitor_agent(
    action: str,
    step_id: str,
    output: str,
    context: Optional[str] = None
) -> str:
    """
    人类监督：日志审查和实时监控
    
    用于确保 Agent 遵循规范，防止不良结果
    可用于：
    - 定期日志审查
    - 关键步骤的实时检查
    - 输出质量监控
    """
    try:
        cli = get_cli()
        
        if action == "log_review":
            # 日志审查模式
            feedback = cli.display_monitor(action, step_id, output, context)
            return feedback
            
        elif action == "realtime_check":
            # 实时检查模式（用于关键步骤）
            logger.info(f"Realtime check for step {step_id}")
            print(f"\n⚡ 实时监控 - 步骤 {step_id}")
            print(f"输出长度：{len(output)} 字符")
            
            # 记录到监控日志
            monitor_log = {
                "timestamp": datetime.now().isoformat(),
                "step_id": step_id,
                "action": action,
                "output_length": len(output),
                "status": "monitored"
            }
            
            logger.info(f"Monitor log: {json.dumps(monitor_log, ensure_ascii=False)}")
            return "monitored"
        
        else:
            return f"Unknown action: {action}"
            
    except Exception as e:
        logger.error(f"Error in monitoring: {e}")
        return f"Error: {str(e)}"