"""测试提示词集 - 简洁验证，低 token 消耗

设计原则：
- 使用小文件避免大 token 消耗
- 验证核心能力而非完整分析
- Mock 模式用于快速验证
"""

from dataclasses import dataclass
from typing import List


@dataclass
class TestCase:
    """测试用例"""

    name: str
    prompt: str
    expected_tools: List[str]
    expected_keywords: List[str]
    description: str = ""


# ========== 基础能力测试（使用小文件）========== #

FILE_OPERATIONS = [
    TestCase(
        name="read_readme",
        prompt="读取 README.md",
        expected_tools=["read_file"],
        expected_keywords=["NanoAgent", "极简", "Agent"],
        description="验证文件读取",
    ),
    TestCase(
        name="read_config",
        prompt="读取 nanoagent.toml",
        expected_tools=["read_file"],
        expected_keywords=["llm", "model", "temperature"],
        description="验证配置文件读取",
    ),
    TestCase(
        name="read_small_file",
        prompt="读取 pyproject.toml 的第一行",
        expected_tools=["read_file"],
        expected_keywords=["dependencies", "requires", "version"],
        description="验证小文件读取",
    ),
]

DIRECTORY_OPERATIONS = [
    TestCase(
        name="list_root",
        prompt="列出当前目录的文件",
        expected_tools=["list_files"],
        expected_keywords=["core", "tests", "examples"],
        description="验证根目录列表",
    ),
    TestCase(
        name="list_examples",
        prompt="列出 examples/ 目录",
        expected_tools=["list_files"],
        expected_keywords=["examples", "py"],
        description="验证子目录列表",
    ),
]

COMMAND_OPERATIONS = [
    TestCase(
        name="simple_list",
        prompt="列出当前目录",
        expected_tools=["list_files"],
        expected_keywords=["core", "tests"],
        description="验证简单列表（mock模式替代命令）",
    ),
    TestCase(
        name="read_version",
        prompt="读取 pyproject.toml 查看版本信息",
        expected_tools=["read_file"],
        expected_keywords=["version", "requires"],
        description="验证版本查询",
    ),
]

# ========== 组合能力测试 ==========

COMPOSITE_OPERATIONS = [
    TestCase(
        name="list_then_read",
        prompt="列出 core/ 目录，然后读取 nanoagent.toml",
        expected_tools=["list_files", "read_file"],
        expected_keywords=["core", "toml", "llm"],
        description="验证多工具组合",
    ),
    TestCase(
        name="analyze_project",
        prompt="读取 CLAUDE.md 总结设计原则",
        expected_tools=["read_file"],
        expected_keywords=["Agent", "clean", "模块", "框架"],
        description="验证理解能力",
    ),
]

# ========== 错误处理测试 ==========

ERROR_HANDLING = [
    TestCase(
        name="file_not_exist",
        prompt="尝试读取不存在的文件 xxx_not_exist.txt",
        expected_tools=["read_file"],
        expected_keywords=["not", "found", "exist", "error", "Error"],
        description="验证错误检测",
    ),
    TestCase(
        name="recover_from_error",
        prompt="读取不存在的文件 xxx.txt，然后列出当前目录",
        expected_tools=["read_file", "list_files"],
        expected_keywords=["error", "not", "found", "core"],
        description="验证错误恢复",
    ),
]

# ========== 全部测试 ==========


def get_all_tests() -> List[TestCase]:
    """获取所有测试用例"""
    all_tests = []
    all_tests.extend(FILE_OPERATIONS)
    all_tests.extend(DIRECTORY_OPERATIONS)
    all_tests.extend(COMMAND_OPERATIONS)
    all_tests.extend(COMPOSITE_OPERATIONS)
    all_tests.extend(ERROR_HANDLING)
    return all_tests


def get_tests_by_category(category: str) -> List[TestCase]:
    """按类别获取测试"""
    categories = {
        "file": FILE_OPERATIONS,
        "directory": DIRECTORY_OPERATIONS,
        "command": COMMAND_OPERATIONS,
        "composite": COMPOSITE_OPERATIONS,
        "error": ERROR_HANDLING,
        "all": get_all_tests(),
    }
    return categories.get(category, [])


def print_test_summary():
    """打印测试摘要"""
    all_tests = get_all_tests()
    print("=" * 60)
    print("NanoAgent 测试套件")
    print("=" * 60)
    print(f"总测试数: {len(all_tests)}")
    print()
    for category, tests in [
        ("文件操作", FILE_OPERATIONS),
        ("目录操作", DIRECTORY_OPERATIONS),
        ("命令执行", COMMAND_OPERATIONS),
        ("组合能力", COMPOSITE_OPERATIONS),
        ("错误处理", ERROR_HANDLING),
    ]:
        print(f"{category} ({len(tests)}):")
        for t in tests:
            print(f"  - {t.name}: {t.description}")
        print()


if __name__ == "__main__":
    print_test_summary()
