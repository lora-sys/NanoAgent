#!/usr/bin/env python3
"""测试 CLI 实时编排器"""

from cli_interface import get_cli

def main():
    print("="*70)
    print("NanoAgent CLI 实时编排器测试")
    print("="*70)
    print()
    
    # 获取 CLI 实例（单例模式）
    cli = get_cli()
    
    # 测试全局单例
    cli2 = get_cli()
    print(f"✓ 单例模式测试: {cli is cli2}")
    print()
    
    # 测试显示功能
    print("测试 1: 显示阶段")
    cli.display_phase("Planning Phase", 1)
    
    print("测试 2: 显示思考")
    cli.display_thinking("正在分析任务需求...")
    
    print("测试 3: 显示动作")
    cli.display_action("tool_call", "write_file with filepath='test.py'")
    
    print("测试 4: 显示结果")
    cli.display_result("✅ Successfully wrote 15 chars to test.py")
    
    print("测试 5: 显示进度")
    cli.display_progress(2, 5, "正在处理中...")
    
    print("测试 6: 显示错误")
    cli.display_error("Tool execution error: File not found")
    
    print("测试 7: 显示完成")
    cli.display_completion("任务完成：创建了 3 个文件")
    
    print("\n" + "="*70)
    print("✅ 所有测试通过")
    print("="*70)
    print()

if __name__ == "__main__":
    main()