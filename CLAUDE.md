# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NanoAgent is a minimalist Agent framework with focus on **clean code, zero magic, and minimal dependencies**.

you first start up venv environment
source .venv/bin/activate


## Commands

```bash
# 执行任务
uv run main.py run "任务描述"

# 交互式对话
uv run main.py chat

# 运行所有测试
uv run pytest

# 运行单个测试
uv run pytest tests/test_chain.py -v

# 代码检查
ruff check . --fix && ruff format .

# 代码格式化
ruff format .
```

## Architecture

```
NanoAgent (core/agent.py)
├── LLM Client (llm/client.py)      # litellm 封装，支持 mock 模式
├── Tool Registry (tools/registry.py) # read_file, list_files, edit_file, run_bash
├── TaskSpec (core/spec.py)         # 轻量任务跟踪
├── Router (core/router.py)         # 智能任务分发
├── PromptChain (core/chain.py)     # 复杂任务拆解
└── ComposableAgent (core/composable.py) # 功能组合层
```

**数据流**: User Task → NanoAgent.run() → LLM + Tools Loop → TaskSpec → JSON Result

## Design Principles (from AGENT.md)

1. **Clean + Zero Magic + Less Dependency** - Prefer builtin functions, no complex abstractions
2. **Keep Code Readable and Clean** - Explicit logic, clear naming
3. **More Use Asyncio Async** - Full async support in routers and chains
4. **Module Design as Framework** - Composable, extensible modules

**ACI Design** (Agent-Computer Interface):
- Tool namespacing for clear boundaries
- Return meaningful context from tools
- Optimize tool responses for token efficiency
- Prompt-engineer tool descriptions

## Key Conventions

- **Mock Mode**: LLM client defaults to mock mode (`mock.enabled=true` in `nanoagent.toml`)
- **Spec Output**: Task results saved to `.spec/*.json`
- **Tool Format**: XML-style `<tool name="xxx" args='{"key":"value"}'/>`
- **Execution Modes**: `traditional` (LLM+Tools loop) vs `chain` (PromptChain)

## Framework Modules

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `core/agent.py` | Main agent loop | `NanoAgent` |
| `core/chain.py` | Task decomposition | `PromptChain`, `ChainStep`, `ChainContext` |
| `core/router.py` | Task routing | `Router`, `Route`, `RouteContext` |
| `core/model_interface.py` | Multi-model support | `ModelRegistry`, `ModelSelector` |
| `core/composable.py` | Feature composition | `ComposableAgent`, `AgentBuilder` |
| `core/spec.py` | Task tracking | `TaskSpec` |
| `llm/client.py` | LLM abstraction | `NanoLLMClient` |
| `tools/registry.py` | Tool management | `ToolRegistry` |

## Dependencies

Minimal core dependencies:
- `litellm` - LLM interface
- `python-dotenv` - Env config
- `typer` - CLI
- `toml` - Config file parsing

Dev: `pytest`, `pytest-asyncio`, `pytest-cov`
