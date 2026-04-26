# Data Model: Agent Parallelization Module

**Feature**: Agent Parallelization Module
**Date**: 2026-04-25

## Core Entities

### TaskNode

Represents a single executable unit in the graph.

| Field | Type | Description |
|-------|------|-------------|
| id | str | Unique identifier |
| name | str | Human-readable name |
| prompt | str | LLM prompt or task description |
| handler | Callable | Optional custom handler function |
| conditions | List[Condition] | Branch conditions for this node |
| timeout | Optional[float] | Seconds before task fails |
| depends_on | List[str] | Node IDs that must complete first |

### Condition

Defines a branching decision point.

| Field | Type | Description |
|-------|------|-------------|
| expression | str | Python-like expression, e.g., `result.contains("error")` |
| then_node | str | Node ID to execute if true |
| else_node | str | Node ID to execute if false |

### ExecutionResult

Result of a single task execution.

| Field | Type | Description |
|-------|------|-------------|
| node_id | str | Which node produced this |
| output | Any | Task output (or None on failure) |
| error | Optional[str] | Error message if failed |
| status | enum | pending / running / completed / failed / cancelled |
| started_at | Optional[float] | Wall clock start time |
| completed_at | Optional[float] | Wall clock end time |
| duration | Optional[float] | Seconds to execute |

### ExecutionGraph

Container for all nodes and their relationships.

| Field | Type | Description |
|-------|------|-------------|
| nodes | Dict[str, TaskNode] | All task nodes by ID |
| entry_point | str | Node ID to start execution from |
| name | str | Graph name for identification |

### ExecutionStatus

Overall execution state.

| Field | Type | Description |
|-------|------|-------------|
| graph | ExecutionGraph | The graph being executed |
| results | Dict[str, ExecutionResult] | Results by node ID |
| strategy | enum | parallel / serial / conditional |
| error_strategy | enum | stop / fail-fast / continue |
| started_at | Optional[float] | Wall clock start |
| completed_at | Optional[float] | Wall clock end |
| total_duration | Optional[float] | Total execution time |

## State Transitions

### TaskNode States

```
pending → running → completed
                  → failed
                  → cancelled
```

### Condition Evaluation

```
input expression
    ↓
evaluate(node.output)
    ↓
True → then_node
False → else_node
```

## Validation Rules

1. Graph must have exactly one entry_point
2. All depends_on references must exist in nodes
3. No cycles allowed (DAG required)
4. Condition expressions must be valid Python-like syntax
5. Timeout must be positive if specified
