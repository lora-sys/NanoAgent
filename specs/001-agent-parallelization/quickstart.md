# Quickstart: Agent Parallelization Module

## Basic Usage

### Parallel Execution

```python
from core.executor import ExecutionGraph, TaskNode, ParallelExecutor

# Create tasks
readme = TaskNode(id="readme", name="Read README", prompt="Summarize README.md")
config = TaskNode(id="config", name="Find Config", prompt="Find all .toml files")

# Build graph
graph = ExecutionGraph(name="file_discovery")
graph.add_node(readme)
graph.add_node(config)
graph.entry_point = "readme"

# Execute in parallel
executor = ParallelExecutor(max_concurrency=5)
results = await executor.run(graph)
```

### Sequential Chain

```python
from core.chain import PromptChain, ChainStep

chain = PromptChain([
    ChainStep("analyze", "Analyze the codebase structure"),
    ChainStep("plan", "Create implementation plan"),
    ChainStep("execute", "Execute the plan"),
])
result = await chain.run(initial_input, llm_client)
```

### Conditional Branching

```python
from core.executor import TaskNode, Condition

check = TaskNode(id="check", name="Check Input", prompt="Validate input")
success = TaskNode(id="success", name="Success Path", prompt="Process normally")
error = TaskNode(id="error", name="Error Path", prompt="Handle error")

# Add condition to check node
check.conditions = [
    Condition(
        expression='result.get("valid", False) == True',
        then_node="success",
        else_node="error"
    )
]
```

## Integration with NanoAgent

```python
from core.agent import NanoAgent

agent = NanoAgent(
    tools=registry,
    llm_client=client,
    executor=ParallelExecutor(max_concurrency=3)  # Optional
)
```

## Error Strategies

```python
# Stop everything on any failure (default)
executor = ParallelExecutor(error_strategy="stop")

# Cancel remaining on first failure
executor = ParallelExecutor(error_strategy="fail-fast")

# Continue even if some tasks fail
executor = ParallelExecutor(error_strategy="continue")
```
