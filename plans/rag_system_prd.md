## Problem Statement

用户需要在 nanoagent 项目中搭建一个完整的 RAG（Retrieval Augmented Generation）知识库问答系统，放在 `examples/rag_demo/` 目录。目标是支持文档上传、智能分块、向量化存储、相似度检索、带溯源引用的回答，以及完整的 E2E 测试。

当前 nanoagent 框架有 LLM 客户端（litellm）、工具注册表、生命周期事件、PromptChain 等基础设施，但没有任何 RAG 相关模块。

## Solution

在 `examples/rag_demo/` 目录下实现一个自包含的 RAG 系统，提供：

1. **文档处理管道** — 上传 → 清洗 → 递归分块 → Embedding → 存储
2. **向量检索** — ChromaDB 向量存储 + 本地 Embedding 模型
3. **RAG 生成** — 带引用的 PromptChain 生成回答
4. **HTTP 服务** — 简单 REST 接口，供前端调用
5. **单页 HTML 前端** — 文件上传、查询、结果展示（含完整引用溯源）
6. **E2E 测试** — 使用 nanoagent eval 框架，覆盖全流程

**设计原则**：非侵入式，框架无关。新模块独立存在，不修改 nanoagent 核心。

## User Stories

### 文档上传
1. 作为用户，我上传一个 TXT/PDF 文件，系统解析并提取纯文本
2. 作为用户，我上传文档后看到上传状态和进度
3. 作为用户，我上传后看到文档被分成了多少个 chunk
4. 作为用户，我重复上传同名文件时系统提示已存在

### 文档清洗
5. 作为用户，文档中的连续空白、特殊字符被自动清理
6. 作为用户，中英文混合文档都能正确处理
7. 作为用户，乱码和无效字符被过滤

### 递归分块
8. 作为用户，文档按段落/句子分块，而非简单截断
9. 作为用户，每个 chunk 有 overlap，相邻块之间有上下文衔接
10. 作为用户，chunk 保留来源信息（file:line）
11. 作为用户，可以配置 chunk 大小和 overlap 比例

### 向量存储与检索
12. 作为用户，上传文档后自动生成 embedding 并存入 ChromaDB
13. 作为用户，输入查询后系统返回最相似的 top-k chunks
14. 作为用户，每个检索结果显示相似度分数
15. 作为用户，查询响应时间 < 2s（不包含 LLM 生成时间）

### Embedding 模型
16. 作为用户，使用本地 embedding 模型（不依赖外部 API）
17. 作为用户，embedding 模型首次调用时自动加载
18. 作为用户，可以切换不同的 embedding 模型

### RAG 生成
19. 作为用户，输入问题后得到基于检索内容的回答
20. 作为用户，每个回答都标注了引用来源（file:line + 相似度 + 原文摘要）
21. 作为用户，点击引用可以高亮对应原文段落
22. 作为用户，系统在检索无相关内容时明确告知"未找到相关内容"

### 前端展示
23. 作为用户，在网页上上传文件并看到上传结果
24. 作为用户，在网页上输入问题并看到回答
25. 作为用户，回答中的每个引用独立展示，显示文件、行号、相似度、摘要
26. 作为用户，可以查看文档列表和已上传文档的 chunk 数量

### 测试
27. 作为开发者，运行 E2E 测试验证上传→检索→回答全流程
28. 作为开发者，单元测试覆盖 pipeline 各环节（loader、cleaner、chunker、embedder、search）
29. 作为开发者，测试验证引用溯源的准确性

## Implementation Decisions

### 目录结构
```
examples/rag_demo/
├── __init__.py
├── config.py              # 配置（chunk_size, overlap, top_k, embedding_model）
├── server.py              # HTTP 服务（/upload, /query, /docs）
├── rag_demo.py            # 入口：python -m examples.rag_demo.rag_demo
├── pipeline/
│   ├── __init__.py
│   ├── document_loader.py   # PDF/TXT 解析
│   ├── text_cleaner.py      # 文本清洗
│   ├── chunker.py          # 递归段落分块
│   └── embedder.py         # 本地 embedding
├── storage/
│   ├── __init__.py
│   ├── chroma_client.py    # ChromaDB CRUD
│   └── document_store.py   # 元数据（文件信息、chunk 映射）
├── retrieval/
│   ├── __init__.py
│   └── search.py           # 向量检索 + rerank
├── generation/
│   └── rag_chain.py       # RAG PromptChain（带引用构造）
├── frontend/
│   └── index.html         # 单页 HTML（上传 + 查询 + 展示）
└── tests/
    ├── __init__.py
    ├── test_pipeline.py    # loader/cleaner/chunker/embedder 单元测试
    ├── test_retrieval.py    # search 单元测试
    └── test_e2e.py        # 端到端测试（eval 框架）
```

### 核心模块接口

**pipeline/document_loader.py**
```python
def load_document(path: str) -> str: ...
def load_txt(path: str) -> str: ...
```

**pipeline/chunker.py**
```python
def recursive_chunk(text: str, chunk_size: int = 512, overlap: int = 100) -> list[dict]:
    # 每个 chunk: {"text": str, "metadata": {"file": str, "start_line": int, "end_line": int}}
```

**pipeline/embedder.py**
```python
class LocalEmbedder:
    def __init__(self, model: str = "sentence-transformers/all-MiniLM-L6-v2")
    def embed(self, texts: list[str]) -> list[list[float]]: ...
    def embed_one(self, text: str) -> list[float]: ...
```

**storage/chroma_client.py**
```python
class ChromaStore:
    def add_chunks(self, chunks: list[dict], embeddings: list[list[float]]): ...
    def search(self, query_embedding: list[float], top_k: int) -> list[dict]: ...
    def delete_by_file(self, filename: str): ...
```

**retrieval/search.py**
```python
def retrieval(query: str, top_k: int = 5) -> list[dict]:
    # 返回: [{"text": str, "score": float, "metadata": dict}, ...]
```

**generation/rag_chain.py**
```python
def generate_with_citations(query: str, chunks: list[dict]) -> dict:
    # 返回: {"answer": str, "citations": [chunk_ref, ...]}
```

### 向量数据库 Schema（ChromaDB）
- Collection name: `nanoagent_rag`
- 每个 chunk 的 metadata: `{"file": str, "start_line": int, "end_line": int, "text": str}`

### Embedding 模型
- 默认: `sentence-transformers/all-MiniLM-L6-v2`（本地运行，384 维）
- 备选: `text-embedding-3-small`（需 OPENAI_API_KEY）

### 分块策略
- 第一层：按 `\n\n` 分割段落
- 第二层：段落内按句子（`.!?` + 换行）重组
- 第三层：超过 chunk_size 的段落按字符固定分割
- Overlap：相邻 chunk 重叠 `overlap` 字符

### RAG Prompt 设计
```
基于以下参考资料回答问题。每个参考都标注了来源。
如果未找到相关内容，直接说明"未找到相关内容"。

## 参考资料
[1] file:core/agent.py:39 | score:0.85
    "class NanoAgent:"

[2] file:core/agent.py:60 | score:0.82
    "def _should_use_chain(self, task: str) -> bool:"

## 问题
{question}

## 回答
```

### HTTP 接口
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/upload` | 上传文件，返回 chunk 数 |
| GET | `/docs` | 列出已上传文档 |
| POST | `/query` | 查询，返回回答 + 引用 |
| DELETE | `/docs/<filename>` | 删除文档 |

### 依赖
- `chromadb`（已有）
- `sentence-transformers`（需安装）
- `pypdf`（需安装，用于 PDF 解析）

## Testing Decisions

### 测试策略
使用 nanoagent 的 `AgentTestHarness` eval 框架风格，在 `tests/test_e2e.py` 中实现：

**Pipeline 单元测试** (`test_pipeline.py`):
- `test_cleaner_removes_whitespace` — 空白字符被清理
- `test_cleaner_removes_invalid_chars` — 乱码被过滤
- `test_chunker_respects_chunk_size` — 每个 chunk 不超过限制
- `test_chunker_includes_overlap` — 相邻 chunk 有 overlap
- `test_chunker_preserves_metadata` — 来源信息完整
- `test_embedder_produces_vectors` — 生成固定维度向量
- `test_embedder_is_deterministic` — 相同文本产生相同向量

**检索单元测试** (`test_retrieval.py`):
- `test_search_returns_top_k` — 返回指定数量结果
- `test_search_includes_scores` — 每个结果含相似度分
- `test_search_preserves_metadata` — metadata 完整

**E2E 测试** (`test_e2e.py`):
- `test_upload_and_query` — 上传文档 → 查询 → 验证回答包含引用
- `test_citation_accuracy` — 引用指向的 chunk 确实包含回答相关内容
- `test_no_false_citation` — 不相关的内容不会被引用

### 测试数据
准备一个 TXT 文件 `tests/fixtures/rag_test_doc.txt`，包含：
- 10 个段落
- 明确的主题（nanoagent 架构描述）
- 可验证的事实性内容

## Out of Scope

- PDF 解析（仅支持 TXT 文件 MVP）
- 多租户/用户隔离
- 增量索引更新
- Reranking 策略（直接用相似度排序）
- LangChain / LlamaIndex 等第三方 RAG 框架集成
- 向量数据库集群部署（单机 ChromaDB 足够）
- 用户认证/权限
- 文档元数据编辑

## Further Notes

### 实现顺序（Phase by Phase）

**Phase 1 — Pipeline**:
1. `config.py` — 配置常量
2. `pipeline/document_loader.py` — TXT 解析
3. `pipeline/text_cleaner.py` — 文本清洗
4. `pipeline/chunker.py` — 递归分块
5. `pipeline/embedder.py` — 本地 embedding
6. 单元测试

**Phase 2 — Storage + Retrieval**:
7. `storage/chroma_client.py` — ChromaDB 存储
8. `storage/document_store.py` — 元数据
9. `retrieval/search.py` — 检索
10. 单元测试

**Phase 3 — Generation**:
11. `generation/rag_chain.py` — RAG PromptChain
12. `server.py` — HTTP 接口

**Phase 4 — Frontend**:
13. `frontend/index.html` — 单页应用
14. 集成测试

**Phase 5 — E2E**:
15. 测试数据准备
16. `tests/test_e2e.py`
17. 完整验证

### 与 nanoagent 框架的关系
- RAG 模块在 `examples/rag_demo/` 下，**不修改任何 core/ 代码**
- 可作为 NanoAgent 的**工具**使用：`rag_upload`, `rag_query`
- `rag_chain.py` 参考了 `core/chain.py` 的 PromptChain 模式

## Implementation Phases

| Phase | Task | Description |
|-------|------|-------------|
| 0 | #4 | Install dependencies + update CLAUDE.md |
| 1 | #5 | Pipeline: loader → cleaner → chunker → embedder |
| 2 | #6 | Storage (ChromaDB) + retrieval layer |
| 3 | #1 | RAG generation chain + HTTP server |
| 4 | #2 | Frontend: single HTML page |
| 5 | #3 | E2E tests + full verification |

**Task IDs**: #1–#6
