"""简化的工具使用测试 - 验证基础功能"""

import asyncio
from core.agent import NanoAgent


async def test_simple_tool_usage():
    """测试简单工具使用"""
    print("🚀 简化工具使用测试")
    print("=" * 80)
    print()

    agent = NanoAgent()

    # 测试提示词
    test_prompts = [
        "读取 README.md 文件的内容",
        "列出当前目录的文件",
        "运行命令 'ls -la'",
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"🎯 测试 {i}/{len(test_prompts)}")
        print(f"📋 提示词: {prompt}")
        print()

        try:
            result = agent.run(prompt, max_iterations=3)

            print(f"✅ 状态: {result.get('status', 'unknown')}")
            print(f"🔧 使用的工具: {result.get('tools_used', [])}")
            print(f"🔄 迭代次数: {result.get('iterations', 0)}")

            if result.get("tools_used"):
                print("✅ 工具使用正常")
            else:
                print("⚠️ 警告: 没有使用任何工具")

            print()
            print("-" * 80)
            print()

        except Exception as e:
            print(f"❌ 错误: {e}")
            print()
            print("-" * 80)
            print()

    print("🎉 测试完成！")


if __name__ == "__main__":
    asyncio.run(test_simple_tool_usage())
