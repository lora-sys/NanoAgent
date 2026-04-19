nanoagent
agent framework
clean + zero magic + less dependcy

more use builtin function
less dependcy
keep it code readable and clean
more use asyncio  async

mouble design as for framework
when create a new feature , add use age to example folder

core:
Maintain simplicity in your agent's design.
Prioritize transparency by explicitly showing the agent’s planning steps.
Carefully craft your agent-computer interface (ACI) through thorough tool documentation and testing.
tool :
-  Choosing the right tools to implement (and not to implement)
-   Namespacing tools to define clear boundaries in functionality
-   Returning meaningful context from tools back to agents
-  Optimizing tool responses for token efficiency
-  Prompt-engineering tool descriptions and specs


evaluation :
Generate real-world evaluation tasks: Avoid overly simplistic "sandbox" environments.
Complex task design: Robust evaluation tasks may require multiple (even dozens of) tool calls.
Verifiable outcomes: Each evaluation prompt should correspond to a verifiable answer or result.
Specify expected tool calls: You can define expected tool sequences to measure whether the agent truly understands tool utility.
Programmatic execution: It is recommended to run evaluations programmatically by directly calling LLM APIs.
Comprehensive metrics collection: Collect various metrics including execution time, number of tool calls, token consumption, and tool errors.
Result analysis: Analyze the results to identify specific areas where the agent encounters difficulties or confusion.

optinal: Building an evaluation measure the performance of your tools,You can  automatically optimize your tools against this evaluation.
rule :
   TDD
   release dependcy
    every change git commit | git push
    must run ruff check --fix &&
    ruff format

## Testing

测试框架：`tests/agent/`

```bash
# unit (mock): uv run pytest tests/agent/ -m unit -v
# integration (real): uv run pytest tests/agent/ -m integration -v
```

新工具测试：
1. `tools/<tool>.py` → 注册 → `core/agent.py` 示例 → `tests/agent/test_<tool>.py`
2. `@mark.unit` + `@mark.integration` 双模式测试
3. `AgentTestHarness.assert_tool_called("tool_name")` 验证工具被调用