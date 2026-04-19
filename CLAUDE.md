# CLAUDE.md

NanoAgent guidance for Claude Code.

## Project

NanoAgent: minimalist Agent framework. **Clean code, zero magic, minimal deps.**

## Setup

```bash
source .venv/bin/activate
```

## Commands

```bash
uv run main.py run "task"           # run task
uv run main.py chat                 # interactive chat
uv run pytest tests/ -v             # run all tests
uv run pytest tests/test_chain.py -v # run single test
ruff check . --fix && ruff format . # lint + format
```

## Architecture

```
NanoAgent (core/agent.py)
├── LLM Client (llm/client.py)       # litellm wrapper, mock mode
├── Tool Registry (tools/registry.py) # read_file, list_files, edit_file, run_bash
├── TaskSpec (core/spec.py)          # task tracking
├── Router (core/router.py)          # task routing
├── PromptChain (core/chain.py)      # task decomposition
├── ComposableAgent (core/composable.py) # feature composition
├── Observability (core/observability.py) # trace, stats
└── Evaluation (core/evaluation.py)  # eval runner
```

Data flow: User Task → NanoAgent.run() → LLM + Tools Loop → TaskSpec → JSON Result

## Design Principles (AGENT.md)

1. **Clean + Zero Magic + Less Dependency** — builtin functions, no complex abstractions
2. **Keep Code Readable and Clean** — explicit logic, clear naming
3. **More Use Asyncio Async** — full async support in routers + chains
4. **Module Design as Framework** — composable, extensible

**ACI Design**:
- Tool namespacing for clear boundaries
- Return meaningful context from tools
- Optimize tool responses for token efficiency
- Prompt-engineer tool descriptions

## Conventions

- **Mock Mode**: LLM client defaults to mock (`mock.enabled=true` in `nanoagent.toml`)
- **Spec Output**: Task results saved to `.spec/*.json`
- **Tool Format**: XML-style `<tool name="xxx" args='{"key":"value"}'/>`
- **Execution Modes**: `traditional` (LLM+Tools loop) vs `chain` (PromptChain)
- **Trace Storage**: SQLite at `~/.nanoagent/traces.db`

## Modules

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `core/agent.py` | Main agent loop | `NanoAgent` |
| `core/chain.py` | Task decomposition | `PromptChain`, `ChainStep`, `ChainContext` |
| `core/router.py` | Task routing | `Router`, `Route`, `RouteContext` |
| `core/model_interface.py` | Multi-model support | `ModelRegistry`, `ModelSelector` |
| `core/composable.py` | Feature composition | `ComposableAgent`, `AgentBuilder` |
| `core/observability.py` | Tracing + stats | `Tracer`, `TraceSession` |
| `core/spec.py` | Task tracking | `TaskSpec` |
| `llm/client.py` | LLM abstraction | `NanoLLMClient` |
| `tools/registry.py` | Tool management | `ToolRegistry` |
| `core/tool_cache.py` | Tool result cache | `ToolResultCache` |
| `tools/grep.py` | ripgrep search | `grep` |

## Dependencies

Core: `litellm`, `python-dotenv`, `typer`, `toml`, `rich`
Dev: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`

## Testing Framework

使用 `tests/agent/` 测试框架，所有工具测试必须使用：

```bash
# Unit tests (mock 模式，不走网络)
uv run pytest tests/agent/ -m unit -v

# Integration tests (real API)
uv run pytest tests/agent/ -m integration -v

# 运行全部 agent 测试
uv run pytest tests/agent/ -v
```

### 测试框架结构

```
tests/agent/
├── harness.py     # AgentTestHarness: mock/real 切换，工具拦截，断言
├── conftest.py    # fixtures: agent_harness, mock_agent, real_agent
├── markers.py     # @unit (mock), @integration (real)
├── fixtures.py    # 预置测试任务库
└── test_*.py     # 各工具测试
```

### 编写新工具测试

```python
from tests.agent.harness import AgentTestHarness

@pytest.mark.unit  # mock 模式
def test_xxx():
    harness = AgentTestHarness(mode="mock")
    harness.load_mock_responses(["<tool name='tool_name' args='{...}'/>", "<response>完成</response>"])
    harness.run_agent("任务描述")
    harness.assert_tool_called("tool_name")

@pytest.mark.integration  # real API
def test_xxx_real():
    harness = AgentTestHarness(mode="real")
    harness.run_agent("任务描述")
    harness.assert_tool_called("tool_name")
```

### 新工具接入清单

1. `tools/<tool>.py` — 实现工具函数
2. `tools/registry.py` — 注册到 `_register_tools()`
3. `core/agent.py` — `_get_system_prompt()` 添加使用示例
4. `pyproject.toml` — 标注系统依赖
5. `tests/agent/test_<tool>.py` — 写用例（@unit + @integration）
6. `uv run pytest tests/agent/test_<tool>.py -v` 验证

### Tool Result Cache

工具结果摘要策略（减少 context token）：

| 工具 | 摘要内容 | 缓存 |
|------|---------|------|
| `grep` | stats（匹配数/文件数） | 完整结果外置 |
| `read_file` | 行数/字符数 | 完整结果外置 |
| `run_bash` | exit_code + output（截断500） | 完整结果外置 |
