"""FlowController - handles conditional branching logic."""

import time
from typing import Any, Dict, Optional

from core.executor.conditions import eval_condition
from core.executor.graph import ExecutionGraph, TaskNode
from core.executor.result import ExecutionResult, ExecutionStatus, TaskStatus
from core.executor.executor import SerialExecutor


class FlowController:
    """Handles conditional branching and flow control."""

    def __init__(self, executor: Optional[SerialExecutor] = None):
        self.executor = executor or SerialExecutor()

    async def execute_with_flow(
        self,
        graph: ExecutionGraph,
        initial_input: Any = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionStatus:
        """
        Execute graph with conditional branching support.

        For nodes with conditions:
        1. Execute the node
        2. Evaluate conditions against the result
        3. Select next node based on condition evaluation
        4. Continue execution
        """
        if context is None:
            context = {}
        if initial_input is not None:
            context["input"] = initial_input

        status = ExecutionStatus(started_at=time.time())
        current_node_id = graph.entry_point

        while current_node_id:
            node = graph.get_node(current_node_id)
            if not node:
                break

            # Execute the node
            result = await self._execute_node(node, context)
            status.add_result(result)
            context[current_node_id] = result.output

            # Check for conditions
            if node.conditions:
                next_node_id = self._evaluate_conditions(node, result)
            else:
                # No conditions - follow depends_on or end
                next_node_id = self._get_next_node(node, graph, status)

            current_node_id = next_node_id

            # Stop on failure
            if result.status == TaskStatus.FAILED:
                break

        status.completed_at = time.time()
        status.total_duration = status.completed_at - status.started_at
        return status

    def _evaluate_conditions(
        self, node: TaskNode, result: ExecutionResult
    ) -> Optional[str]:
        """Evaluate conditions and return next node ID."""
        for condition in node.conditions:
            condition_met = eval_condition(condition.expression, result.output)
            if condition_met:
                return condition.then_node
            else:
                return condition.else_node
        return None

    def _get_next_node(
        self,
        node: TaskNode,
        graph: ExecutionGraph,
        status: ExecutionStatus,
    ) -> Optional[str]:
        """Get the next node to execute based on dependencies."""
        # Find nodes that depend on current node and are ready
        for other_id, other_node in graph.nodes.items():
            if other_id == node.id:
                continue
            if node.id in other_node.depends_on:
                # Check if all dependencies are met
                all_deps_met = all(
                    status.get_result(dep_id) is not None
                    for dep_id in other_node.depends_on
                )
                if all_deps_met:
                    return other_id
        return None

    async def _execute_node(
        self, node: TaskNode, context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a single node using the executor."""
        return await self.executor._execute_node(node, context)
