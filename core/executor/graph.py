"""Execution graph - DAG of tasks with dependencies."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set


@dataclass
class Condition:
    """Defines a branching decision point."""

    expression: (
        str  # Python-like expression, e.g., `result.get("valid", False) == True`
    )
    then_node: str  # Node ID to execute if true
    else_node: str  # Node ID to execute if false

    def to_dict(self) -> Dict[str, Any]:
        return {
            "expression": self.expression,
            "then_node": self.then_node,
            "else_node": self.else_node,
        }


@dataclass
class TaskNode:
    """Represents a single executable unit in the graph."""

    id: str
    name: str
    prompt: str = ""
    handler: Optional[Callable] = None
    conditions: List[Condition] = field(default_factory=list)
    timeout: Optional[float] = None
    depends_on: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "prompt": self.prompt,
            "conditions": [c.to_dict() for c in self.conditions],
            "timeout": self.timeout,
            "depends_on": self.depends_on,
        }


class ExecutionGraph:
    """Container for all nodes and their relationships."""

    def __init__(self, name: str = "default"):
        self.name = name
        self.nodes: Dict[str, TaskNode] = {}
        self.entry_point: Optional[str] = None

    def add_node(self, node: TaskNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node

    def get_node(self, node_id: str) -> Optional[TaskNode]:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the graph."""
        if node_id in self.nodes:
            del self.nodes[node_id]
            # Remove from depends_on lists
            for node in self.nodes.values():
                if node_id in node.depends_on:
                    node.depends_on.remove(node_id)
            return True
        return False

    def validate(self) -> List[str]:
        """Validate the graph. Returns list of error messages."""
        errors = []

        # Must have exactly one entry point
        if not self.entry_point:
            errors.append("Graph must have an entry_point")
        elif self.entry_point not in self.nodes:
            errors.append(f"entry_point '{self.entry_point}' not found in nodes")

        # All depends_on references must exist
        for node_id, node in self.nodes.items():
            for dep_id in node.depends_on:
                if dep_id not in self.nodes:
                    errors.append(
                        f"Node '{node_id}' depends on non-existent node '{dep_id}'"
                    )

        # Check for cycles
        cycle = self._find_cycle()
        if cycle:
            errors.append(f"Graph contains a cycle: {' -> '.join(cycle)}")

        return errors

    def _find_cycle(self) -> Optional[List[str]]:
        """Detect cycles using DFS. Returns cycle path or None."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node_id: str) -> Optional[List[str]]:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            node = self.nodes.get(node_id)
            if node:
                for dep_id in node.depends_on:
                    if dep_id not in visited:
                        result = dfs(dep_id)
                        if result:
                            return result
                    elif dep_id in rec_stack:
                        cycle_start = path.index(dep_id)
                        return path[cycle_start:] + [dep_id]

            path.pop()
            rec_stack.remove(node_id)
            return None

        for node_id in self.nodes:
            if node_id not in visited:
                result = dfs(node_id)
                if result:
                    return result

        return None

    def get_execution_order(self) -> List[str]:
        """Get topologically sorted execution order for serial execution."""
        in_degree: Dict[str, int] = {node_id: 0 for node_id in self.nodes}

        for node in self.nodes.values():
            for dep_id in node.depends_on:
                in_degree[node.id] += 1

        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node_id = queue.pop(0)
            result.append(node_id)

            for other_node in self.nodes.values():
                if node_id in other_node.depends_on:
                    in_degree[other_node.id] -= 1
                    if in_degree[other_node.id] == 0:
                        queue.append(other_node.id)

        if len(result) != len(self.nodes):
            raise ValueError("Graph has cycles, cannot determine execution order")

        return result

    def get_parallel_batches(self) -> List[List[str]]:
        """Group nodes into batches that can execute in parallel."""
        batches: List[List[str]] = []
        remaining = set(self.nodes.keys())

        while remaining:
            # Find nodes with all dependencies satisfied
            batch = []
            for node_id in list(remaining):
                node = self.nodes[node_id]
                if all(dep not in remaining for dep in node.depends_on):
                    batch.append(node_id)

            if not batch:
                raise ValueError("Graph has cycles, cannot batch")

            batches.append(batch)
            remaining -= set(batch)

        return batches

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "entry_point": self.entry_point,
        }
