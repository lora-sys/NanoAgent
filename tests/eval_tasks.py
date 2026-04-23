"""评估任务定义 — 格式：prompt + expected + verify_type

定义任务只需：
    Task(prompt="...", expected=["keyword"], verify="contains")
    Task(prompt="...", expected_tools=["read_file"], verify="tools")

verify_type:
    contains  - 响应包含关键词
    tools     - 调用了指定工具
    semantic  - LLM 判断语义相近（较慢）
    exact     - 精确匹配
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    prompt: str
    expected: list[str] | str = ""          # contains: list[str]; tools: ""
    verify_type: str = "contains"            # contains | tools | semantic | exact
    name: str = ""
    difficulty: str = "basic"               # basic | intermediate
    expected_tools: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.name:
            import re
            words = re.findall(r'\w+', self.prompt)[:3]
            self.name = "_".join(words).lower()

# ─── 任务库 ──────────────────────────────────────────────────────────────────

TASKS: list[Task] = [

    # ══ 文件读写 ══════════════════════════════════════════════════════════════
    Task(
        name="read_file_readme",
        prompt="读取项目根目录的 README.md 文件，告诉我这个项目叫什么名字",
        expected=["NanoAgent"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["read_file"],
    ),
    Task(
        name="read_file_pyproject",
        prompt="读取 pyproject.toml 文件，告诉我项目名称和版本号",
        expected=["nanoagent"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["read_file"],
    ),
    Task(
        name="read_file_core_agent",
        prompt="读取 core/agent.py 的前 20 行代码",
        expected=["NanoAgent"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["read_file"],
    ),

    # ══ 目录列表 ═══════════════════════════════════════════════════════════════
    Task(
        name="list_files_project",
        prompt="列出项目根目录的所有文件和文件夹",
        expected="",
        verify_type="tools",
        difficulty="basic",
        expected_tools=["list_files"],
    ),
    Task(
        name="list_files_examples",
        prompt="列出 examples/ 目录下的所有文件",
        expected=["examples"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["list_files"],
    ),
    Task(
        name="list_files_tests",
        prompt="列出 tests/ 目录下有哪些测试文件",
        expected=["tests"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["list_files"],
    ),

    # ══ 代码搜索 ══════════════════════════════════════════════════════════════
    Task(
        name="grep_function_defs",
        prompt="在 core/ 目录下搜索所有以 'def ' 开头的行（函数定义），列出前 5 个",
        expected=["def"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["grep"],
    ),
    Task(
        name="grep_imports",
        prompt="在 core/agent.py 中搜索所有 import 语句",
        expected=["import"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["grep"],
    ),
    Task(
        name="grep_class_defs",
        prompt="在 tools/ 目录下搜索包含 'class ' 的行（类定义）",
        expected=["class"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["grep"],
    ),

    # ══ Bash 命令 ═════════════════════════════════════════════════════════════
    Task(
        name="run_bash_pwd",
        prompt="运行 'pwd' 命令，显示当前工作目录",
        expected="",
        verify_type="tools",
        difficulty="basic",
        expected_tools=["run_bash"],
    ),
    Task(
        name="run_bash_ls",
        prompt="运行 'ls -la' 命令，列出目录内容",
        expected="",
        verify_type="tools",
        difficulty="basic",
        expected_tools=["run_bash"],
    ),
    Task(
        name="run_bash_git_status",
        prompt="运行 'git status --short' 命令，显示 git 状态",
        expected="",
        verify_type="tools",
        difficulty="basic",
        expected_tools=["run_bash"],
    ),

    # ══ 多工具组合 ═══════════════════════════════════════════════════════════
    Task(
        name="multi_read_and_list",
        prompt="先列出 tests/ 目录，再读取其中的一个 .py 文件",
        expected="",
        verify_type="tools",
        difficulty="intermediate",
        expected_tools=["list_files", "read_file"],
    ),
    Task(
        name="multi_search_and_read",
        prompt="在 core/ 下搜索包含 'class NanoAgent' 的文件，然后读取该文件",
        expected="",
        verify_type="tools",
        difficulty="intermediate",
        expected_tools=["grep", "read_file"],
    ),
    Task(
        name="multi_list_and_grep",
        prompt="列出 tools/ 目录，然后在其中搜索包含 'def ' 的行",
        expected="",
        verify_type="tools",
        difficulty="intermediate",
        expected_tools=["list_files", "grep"],
    ),

    # ══ 生命周期 ══════════════════════════════════════════════════════════════
    Task(
        name="lifecycle_single_turn",
        prompt="简单回复：你好",
        expected=["你好", "nanoagent", "NanoAgent"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=[],
    ),
    Task(
        name="lifecycle_with_tool",
        prompt="读取 README.md 并告诉我项目名称",
        expected=["NanoAgent"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["read_file"],
    ),
    Task(
        name="lifecycle_multi_tool",
        prompt="列出 tests/ 目录，然后读取 README.md",
        expected="",
        verify_type="tools",
        difficulty="intermediate",
        expected_tools=["list_files", "read_file"],
    ),

    # ══ Chain 提示链 ═════════════════════════════════════════════════════════
    Task(
        name="chain_mode_analysis",
        prompt="提示链 帮我分析 nanoagent 项目的整体架构",
        expected=["core", "agent", "模块"],
        verify_type="contains",
        difficulty="intermediate",
        expected_tools=[],
    ),
    Task(
        name="chain_mode_summary",
        prompt="提示链 总结这个项目的核心功能和设计原则",
        expected=["NanoAgent", "功能", "设计"],
        verify_type="contains",
        difficulty="intermediate",
        expected_tools=[],
    ),
    Task(
        name="chain_mode_structure",
        prompt="提示链 分析 core/ 目录的代码结构设计",
        expected=["core", "模块", "代码"],
        verify_type="contains",
        difficulty="intermediate",
        expected_tools=[],
    ),

    # ══ 可观测性 ════════════════════════════════════════════════════════════
    Task(
        name="observability_basic",
        prompt="列出 tests/ 目录的内容",
        expected="",
        verify_type="tools",
        difficulty="basic",
        expected_tools=["list_files"],
    ),
    Task(
        name="observability_grep",
        prompt="在 core/ 下搜索包含 'lifecycle' 的文件",
        expected=["lifecycle", "core"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["grep"],
    ),
    Task(
        name="observability_read",
        prompt="读取 README.md 的第一段",
        expected=["NanoAgent"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["read_file"],
    ),

    # ══ Tool Result Cache ════════════════════════════════════════════════════
    Task(
        name="cache_grep_result",
        prompt="在 core/ 下搜索 'class ' 关键字",
        expected=["class"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["grep"],
    ),
    Task(
        name="cache_read_result",
        prompt="读取 core/agent.py 的前 5 行",
        expected=["NanoAgent"],
        verify_type="contains",
        difficulty="basic",
        expected_tools=["read_file"],
    ),
    Task(
        name="cache_list_result",
        prompt="列出项目根目录的所有内容",
        expected="",
        verify_type="tools",
        difficulty="basic",
        expected_tools=["list_files"],
    ),
]