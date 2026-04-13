"""NanoAgent CLI entry point."""

import sys
from dotenv import load_dotenv

load_dotenv()

from core.agent_loop import NanoAgent  # noqa: E402

DEFAULT_TASK = (
    "我要为一个名为'SmartHome AI'的智能家居公司开发一个完整的商业计划书和产品展示网站。"
    "具体需求："
    "1. 核心业务：智能家居控制系统，包括语音助手、设备联动、自动化场景"
    "2. 目标受众：投资人和潜在合作伙伴"
    "3. 前端用途：产品演示和商业展示"
    "4. 技术栈：React + TypeScript"
    "5. 设计风格：现代科技感，蓝色主题"
    "6. 功能要求："
    "- 首页展示产品核心功能"
    "- 产品特性介绍页面"
    "- 技术架构图展示"
    "- 联系我们表单（带验证）"
    "- 响应式设计"
    "7. 交付格式：完整的 React 项目代码 + 部署说明文档"
)


def get_task() -> str:
    return " ".join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_TASK


if __name__ == "__main__":
    agent = NanoAgent()
    result = agent.run(get_task())
    print(result)
