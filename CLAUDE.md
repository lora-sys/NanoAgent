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

## Dependencies

Core: `litellm`, `python-dotenv`, `typer`, `toml`, `rich`
Dev: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff`
