#!/usr/bin/env python3
"""
NanoAgent 完整使用示例

演示如何使用 CLI 界面与 Agent 交互
"""

from core.agent_loop import NanoAgent

def main():
    print("="*70)
    print("NanoAgent - 智能任务执行系统")
    print("="*70)
    print()
    
    # 创建 Agent（会自动初始化 CLI 界面）
    agent = NanoAgent()
    
    # 示例任务
    task = """
    创建一个简单的 Python 计算器脚本，支持以下功能：
    - 加法、减法、乘法、除法
    - 用户友好的命令行界面
    - 错误处理
    
    请编写代码并测试
    """
    
    print(f"📝 任务：{task.strip()}")
    print()
    
    # 运行任务（CLI 界面会自动显示进度）
    result = agent.run(task)
    
    # 显示最终结果
    print()
    print("="*70)
    print("📊 执行结果")
    print("="*70)
    print(result)
    print()
    
    # 提示查看生成的文件
    print("💡 提示：查看 agent_workspace/ 目录查看生成的文件")
    print("💡 提示：查看 nanoagent.log 获取详细日志")
    print()

if __name__ == "__main__":
    main()