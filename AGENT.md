 Nano Agent Specification

> **Core Philosophy**: Nano = Minimal dependencies + Clear layers. 
> Delivery-first, zero-magic, and async-native. Keep it lean, keep it fast.

1. Tech Stack (The "No-Bloat" Rule)
*   **Schema & State**: `pydantic` (Source of truth for config, state, and tool schemas).
*   **I/O**: `httpx` + `asyncio` (Async-first for all external calls & RAG).
*   **Logging**: `structlog` or `rich` (Transparent thinking; matches `soul.md`).
*   **CLI**: `typer` (For a one-command dev experience).
*   **Package Management**: `uv` + `pyproject.toml`.
*   **Templating**: `jinja2` (All prompts stored in `templates/*.jinja2`).

 2. Architecture & Design
*   **Clean Architecture**: Stick to dedicated folders; never let LangChain/LlamaIndex bloat creep in.
*   **Async-First**: Use `async/await` everywhere. Speed matters; LLM calls are the only allowed bottleneck.
*   **Complexity Cap**: The core agent loop must be **< 300 lines**.
*   **Pluggable by Design**: Skills, memory, RAG, and sandbox must be swappable in one line.
*   **Zero Magic**: Everything must be visible, debuggable, and documented with parameters schemas.

 3. Developer Experience (DX)
*   **One-Command Quickstart**: `nanoagent run "task"` (e.g., `nanoagent run "build me a todo app"`).
*   **@skill Decorator**: Use a single decorator to auto-register functions. Skills live in `skills/` or as pip packages.
*   **Schema Automation**: Auto-generate OpenAI/Anthropic tool schemas directly from Pydantic.
*   **Config**: Centralized management via `nanoagent.toml`.

  4.Optimization & Guardrails
*   **Smart Caching**: Use `@cache` on prompt templates and embedding lookups.
*   **State Compression**: Keep only recent messages + summaries in context to save tokens.
*   **Loop Protection**: Max-steps + early reflection to avoid infinite loops.
*   **No Status Files**: Don't write junk files; keep the execution environment clean.

5. Quality & Delivery
*   **Testing**: Heavily mock LLM responses in `tests/`.
*   **Documentation**: Docstrings and examples in every file.
*   **Versioning**: Strict semantic versioning from day one.
6 . More use builtin function
*   python builtin mouble function
7.  Agent use mark signal communcation protocol
    example
    "" 
    <|thinking|>
    <|/thinking|>
    """ 
