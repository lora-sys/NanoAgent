#!/usr/bin/env python3
"""
NanoAgent CLI 实时编排器 - 完整演示

展示 CLI 如何实时显示执行流程和与用户交互
"""

from cli_interface import get_cli

def simulate_agent_execution():
    """模拟 Agent 执行流程"""
    cli = get_cli()
    
    # 显示头部
    cli.display_header()
    
    # 模拟任务分析
    cli.display_phase("任务分析")
    cli.display_result("任务类型: code", True)
    cli.display_result("置信度: 95.00%", True)
    
    # 模拟规划阶段
    cli.display_phase("Planning Phase")
    cli.display_thinking("正在制定执行计划...")
    cli.display_result("计划生成: 5 个步骤", True)
    
    # 模拟执行阶段
    cli.display_phase("Execution Phase")
    
    # 步骤 1
    cli.display_progress(1, 5, "创建项目结构")
    cli.display_thinking("分析需求...")
    cli.display_action("tool_call", "write_file (参数: filepath, content)")
    cli.display_result("✅ Successfully wrote 150 chars to main.py", True)
    
    # 步骤 2
    cli.display_progress(2, 5, "实现核心功能")
    cli.display_thinking("分析当前状态...")
    cli.display_action("tool_call", "write_file (参数: filepath, content)")
    cli.display_result("✅ Successfully wrote 280 chars to auth.py", True)
    
    # 步骤 3 - HITL 交互
    cli.display_progress(3, 5, "等待用户输入")
    cli.display_thinking("需要用户偏好...")
    
    # 模拟用户交互（实际执行时会暂停等待用户输入）
    print("\n💡 注意：以下是模拟的 HITL 交互（实际执行时会暂停等待用户输入）")
    print("真实场景中，Agent 会暂停并显示类似以下界面：\n")
    
    # 模拟问题界面
    print("============================================================")
    print("🤔 Agent 需要你的帮助：")
    print("============================================================")
    print()
    print("问题：你希望使用哪个数据库？")
    print()
    print("可选答案：")
    print("  1. PostgreSQL")
    print("  2. MySQL")
    print("  3. SQLite")
    print()
    print("============================================================")
    print()
    print("用户输入：PostgreSQL")
    print()
    
    cli.display_result("用户选择: PostgreSQL", True)
    
    # 步骤 4
    cli.display_progress(4, 5, "添加错误处理")
    cli.display_thinking("分析错误场景...")
    cli.display_action("tool_call", "write_file (参数: filepath, content)")
    cli.display_result("✅ Successfully wrote 120 chars to error.py", True)
    
    # 步骤 5
    cli.display_progress(5, 5, "运行测试")
    cli.display_thinking("检查代码...")
    cli.display_action("tool_call", "write_file (参数: filepath, content)")
    cli.display_result("✅ Successfully wrote 180 chars to test.py", True)
    
    # 反思阶段
    cli.display_phase("Reflection Phase")
    cli.display_thinking("反思执行结果...")
    cli.display_result("反思确认任务完成", True)
    
    # 显示完成
    cli.display_completion(f"执行完成 - 共 5 步\n生成的文件：main.py, auth.py, error.py, test.py")
    
    # 显示尾部
    cli.display_footer()

def main():
    print("="*70)
    print("NanoAgent CLI 实时编排器 - 完整演示")
    print("="*70)
    print()
    print("本演示展示 CLI 如何：")
    print("  ✓ 实时显示 Agent 执行流程")
    print("  ✓ 与用户交互（HITL）")
    print("  ✓ 性能跟踪（计时）")
    print("  ✓ 模块化设计")
    print()
    print("="*70)
    print()
    
    simulate_agent_execution()
    
    print("="*70)
    print("🎉 演示完成")
    print("="*70)
    print()
    print("💡 下一步：")
    print("  运行 'python example_usage.py' 查看真实的 Agent 执行")
    print("  查看 CLI_GUIDE.md 了解详细使用指南")
    print()

if __name__ == "__main__":
    main()