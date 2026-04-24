"""RAG 评测任务定义

基于 rag_test_doc.txt fixture 设计，覆盖：
- 有明确答案的问题（grounded）
- 文档中不存在的问题（hallucination test）
- 部分可回答的问题（partial）
- 引用精度测试

verify_type:
    rag_grounded    — 答案包含关键词 AND 有有效引用
    rag_no_citation — 无文档支持时应无引用（hallucination test）
    rag_partial     — 部分可答，部分未答
"""

from dataclasses import dataclass, field


@dataclass
class RAGTask:
    """RAG 评测任务."""
    name: str
    prompt: str
    # 验证方式
    verify_type: str = "rag_grounded"  # rag_grounded | rag_no_citation | rag_partial
    # rag_grounded: 答案应包含以下关键词（all must appear）
    expected_keywords: list[str] = field(default_factory=list)
    # rag_grounded: 至少需要有效引用的数量
    min_citations: int = 1
    # rag_grounded: 所有引用最低分数阈值
    min_avg_score: float = 0.0
    # RAG 查询参数
    rag_top_k: int = 5
    rag_min_score: float = 0.3
    difficulty: str = "basic"


# ─── 任务库 ───────────────────────────────────────────────────────────────────

TASKS_RAG: list[RAGTask] = [

    # ══ 有明确答案：NanoAgent 基础 ═══════════════════════════════════════════

    RAGTask(
        name="rag_nanoagent_what",
        prompt="NanoAgent 是什么？",
        verify_type="rag_grounded",
        expected_keywords=["框架", "模块化", "Python"],
        min_citations=1,
        rag_top_k=3,
        rag_min_score=0.25,
    ),

    RAGTask(
        name="rag_core_components",
        prompt="NanoAgent 的核心组件有哪些？",
        verify_type="rag_grounded",
        expected_keywords=["主循环", "LLM", "工具"],
        min_citations=1,
        rag_top_k=5,
        rag_min_score=0.25,
    ),

    RAGTask(
        name="rag_llm_client",
        prompt="LLM 客户端基于什么库？支持哪些功能？",
        verify_type="rag_grounded",
        expected_keywords=["litellm", "流式", "同步"],
        min_citations=1,
        rag_top_k=3,
        rag_min_score=0.25,
    ),

    RAGTask(
        name="rag_tool_registry",
        prompt="工具注册表支持哪些工具？",
        verify_type="rag_grounded",
        expected_keywords=["read_file", "run_bash", "grep"],
        min_citations=1,
        rag_top_k=3,
        rag_min_score=0.25,
    ),

    RAGTask(
        name="rag_lifecycle",
        prompt="生命周期事件系统有几层？",
        verify_type="rag_grounded",
        expected_keywords=["三层", "嵌套"],
        min_citations=1,
        rag_top_k=3,
        rag_min_score=0.25,
    ),

    RAGTask(
        name="rag_observability",
        prompt="可观测性追踪哪些内容？存在哪里？",
        verify_type="rag_grounded",
        expected_keywords=["LLM", "工具", "SQLite"],
        min_citations=1,
        rag_top_k=3,
        rag_min_score=0.25,
    ),

    RAGTask(
        name="rag_tool_cache",
        prompt="ToolResultCache 减少什么开销？",
        verify_type="rag_grounded",
        expected_keywords=["token", "LRU"],
        min_citations=1,
        rag_top_k=3,
        rag_min_score=0.25,
    ),

    # ══ Hallucination 测试：文档中没有的内容 ══════════════════════════════════

    RAGTask(
        name="rag_hallucination_worldcup",
        prompt="谁赢得了2024年世界杯冠军？",
        verify_type="rag_no_citation",
        expected_keywords=[],
        min_citations=0,
        rag_top_k=5,
        rag_min_score=0.3,
    ),

    RAGTask(
        name="rag_hallucination_president",
        prompt="NanoAgent 的创始人是哪位？",
        verify_type="rag_no_citation",
        expected_keywords=[],
        min_citations=0,
        rag_top_k=5,
        rag_min_score=0.3,
    ),

    RAGTask(
        name="rag_hallucination_funding",
        prompt="NanoAgent 融资金额是多少？",
        verify_type="rag_no_citation",
        expected_keywords=[],
        min_citations=0,
        rag_top_k=5,
        rag_min_score=0.3,
    ),

    # ══ 路由 + chain：Embedding 对中文词根匹配弱，放低阈值 ═════════════════════

    RAGTask(
        name="rag_router_strategies",
        prompt="路由器支持哪些路由策略？",
        verify_type="rag_grounded",
        expected_keywords=["关键词", "函数", "智能"],
        min_citations=1,
        rag_top_k=5,
        rag_min_score=0.1,  # 低阈值因为中文 embedding 匹配弱
    ),

    RAGTask(
        name="rag_chain_mode",
        prompt="NanoAgent 有哪些预定义链？",
        verify_type="rag_grounded",
        expected_keywords=["analysis", "design", "chain"],
        min_citations=1,
        rag_top_k=3,
        rag_min_score=0.25,
    ),

    RAGTask(
        name="rag_testing_framework",
        prompt="NanoAgent 有哪些测试方式？",
        verify_type="rag_grounded",
        expected_keywords=["单元测试", "集成测试", "Mock"],
        min_citations=1,
        rag_top_k=3,
        rag_min_score=0.25,
    ),

]
