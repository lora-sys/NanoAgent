"""Memory eval tasks — 验证记忆系统功能."""

from dataclasses import dataclass, field


@dataclass
class MemoryTask:
    """Memory-specific eval task."""

    name: str
    prompt: str
    expected: list[str] | str = ""
    verify_type: str = "contains"  # contains | tools | semantic | exact
    difficulty: str = "basic"  # basic | intermediate | advanced
    memory_type: str = (
        "long_term"  # short_term | working | long_term | preference | cross_session
    )
    expected_tools: list[str] = field(default_factory=list)
    verify_recall: bool = False  # Verify memory was stored/retrieved across sessions
    description: str = ""


MEMORY_TASKS = [
    # ─── Preference Memory ──────────────────────────────────────────────────
    MemoryTask(
        name="memory_preference_set",
        prompt="设置我的名字是Alice",
        expected=["ok"],
        verify_type="contains",
        difficulty="basic",
        memory_type="preference",
        description="Set a preference (name)",
    ),
    MemoryTask(
        name="memory_preference_get",
        prompt="我的名字是什么？",
        expected=["Alice"],
        verify_type="contains",
        difficulty="basic",
        memory_type="preference",
        verify_recall=True,
        description="Get a preference after setting",
    ),
    MemoryTask(
        name="memory_preference_list",
        prompt="列出我所有的偏好设置",
        expected=["name", "Alice"],
        verify_type="contains",
        difficulty="basic",
        memory_type="preference",
        description="List all preferences",
    ),
    # ─── Long-term Memory ──────────────────────────────────────────────────
    MemoryTask(
        name="memory_long_term_store",
        prompt="记住项目的核心模块是agent、tools和llm",
        expected=["ok"],
        verify_type="contains",
        difficulty="basic",
        memory_type="long_term",
        description="Store information in long-term memory",
    ),
    MemoryTask(
        name="memory_long_term_recall",
        prompt="项目的核心模块有哪些？",
        expected=["agent", "llm"],
        verify_type="contains",
        difficulty="intermediate",
        memory_type="long_term",
        verify_recall=True,
        description="Recall stored information from long-term memory",
    ),
    MemoryTask(
        name="memory_forget",
        prompt="忘记我之前设置的名字",
        expected=["ok"],
        verify_type="contains",
        difficulty="basic",
        memory_type="long_term",
        description="Delete information from memory",
    ),
    # ─── Working Memory ───────────────────────────────────────────────────
    MemoryTask(
        name="memory_working_store",
        prompt="记住当前任务的工作进度是完成了第一步",
        expected=["ok"],
        verify_type="contains",
        difficulty="basic",
        memory_type="working",
        description="Store in working memory",
    ),
    MemoryTask(
        name="memory_working_recall",
        prompt="我当前任务的工作进度是什么？",
        expected=["第一步", "完成"],
        verify_type="contains",
        difficulty="basic",
        memory_type="working",
        verify_recall=True,
        description="Recall from working memory",
    ),
    # ─── Cross-session Memory ────────────────────────────────────────────
    MemoryTask(
        name="memory_cross_session_recall",
        prompt="我上一个任务做了什么？",
        expected=["session"],
        verify_type="contains",
        difficulty="intermediate",
        memory_type="cross_session",
        verify_recall=True,
        description="Recall from previous session",
    ),
    MemoryTask(
        name="memory_search",
        prompt="搜索我之前关于nanoagent的任务",
        expected=["session"],
        verify_type="contains",
        difficulty="intermediate",
        memory_type="cross_session",
        description="Search across session history",
    ),
    # ─── Memory Status ────────────────────────────────────────────────────
    MemoryTask(
        name="memory_status",
        prompt="查看记忆系统状态",
        expected=["ok"],
        verify_type="contains",
        difficulty="basic",
        memory_type="preference",
        description="Check memory system status",
    ),
    # ─── Token Optimization ───────────────────────────────────────────────
    MemoryTask(
        name="memory_token_budget",
        prompt="验证token预算是否正确管理",
        expected=[],
        verify_type="contains",
        difficulty="intermediate",
        memory_type="working",
        description="Verify token budget is respected",
    ),
    # ─── Hot-swap Store ───────────────────────────────────────────────────
    MemoryTask(
        name="memory_hot_swap",
        prompt="验证记忆存储热插拔功能",
        expected=["ok"],
        verify_type="contains",
        difficulty="advanced",
        memory_type="long_term",
        description="Verify hot-swap of memory store works",
    ),
]


def get_memory_tasks() -> list[MemoryTask]:
    return list(MEMORY_TASKS)
