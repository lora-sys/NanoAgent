# NanoAgent Constitution

## Core Principles

### I. Clean & Zero Magic
Code must be readable without magic. No hidden control flow, no implicit state. Explicit logic over clever tricks. Every abstraction must earn its weight.

### II. Minimal Dependencies
Every dependency is a liability. Prefer stdlib > single lib > new lib. When adding deps: justify cost vs. benefit. No organizational-only libraries.

### III. Test-First (Non-Negotiable)
TDD mandatory for new features: Tests written first, user approves, tests fail, then implement. Red-Green-Refactor strictly enforced. Coverage ≥ 80% for new code.

### IV. Hot-Swap Architecture
All core components (memory, LLM, tools) must be pluggable at runtime. No hardcoded implementations. Registry pattern for extensibility.

### V. Token Efficiency
Context is expensive. Optimize for minimal tokens, maximum effectiveness. Language-aware token estimation. Truncate intelligently, preserve meaning.

## Testing Standards

### Unit Tests
- All tools require `@unit` mock-mode tests
- harness.py provides mock/real toggle, tool interception, assertions
- Each new tool: minimum 3 unit tests (happy path, error, edge case)

### Integration Tests
- `@integration` tests run against real API
- Marked clearly, skipped in CI unless explicitly triggered
- Use real_agent fixture for end-to-end flows

### Eval Framework
- Every feature needs eval tasks in eval_tasks.py
- verify_type="tools" preferred over verify_type="contains"
- Eval runner: `uv run python tests/eval.py`

## User Experience Consistency

### Tool Interface Contract
- Tools return dict with status field: `{"status": "ok"}` or `{"status": "error", "message": "..."}`
- XML-style tool call format: `<tool name="xxx" args='{"key":"value"}'/>`
- Response format: `<response>...</response>` or `<error>...</error>`

### Memory Tool Semantics
- `remember` defaults to long_term, persists across sessions
- `recall` defaults to cross_session, searches session history
- `forget` removes from specified memory store
- `preference` manages user settings (get/set/list)

### Agent Response Contract
- Always use tools for file/system queries, never guess
- Memory context injected at agent start (max 1500 tokens default)
- Task results saved to .spec/*.json

## Performance Requirements

### Token Budgets
| Memory Type | Tool-Heavy | Analysis | Creative |
|-------------|------------|----------|----------|
| preference  | 150        | 100      | 200      |
| cross_session | 200     | 500      | 300      |
| long_term   | 200        | 500      | 400      |
| working     | 350        | 150      | 200      |
| short_term  | 150        | 50       | 200      |

### Optimization Rules
- Language-aware token estimation (Chinese ~1.8 chars/token, English ~4 chars/token)
- Sentence-aware truncation preserves complete sentences
- Deduplicate across memory stores before context injection
- Hard tokens limits never exceeded

### Memory Hot-Swap
- Register new stores at runtime via MemoryManager.register_store()
- Stores must implement BaseMemory ABC
- No restart required for memory system changes

## Governance

Constitution supersedes all other practices. Amendments require:
1. Documentation of proposed change
2. Migration plan for existing code
3. Approval from project lead

All PRs must verify compliance with these principles.

**Version**: 1.0.0 | **Ratified**: 2026-04-25 | **Last Amended**: 2026-04-25
