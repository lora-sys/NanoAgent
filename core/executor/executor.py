"""Parallel and Serial executors for task graphs."""

import asyncio
import time
from typing import Any, Dict, List, Optional

from core.executor.graph import ExecutionGraph, TaskNode
from core.executor.result import (
    ErrorStrategy,
    ExecutionResult,
    ExecutionStatus,
    ExecutionStrategy,
    TaskStatus,
)


class BaseExecutor:
    """Base executor with common functionality."""

    def __init__(
        self,
        error_strategy: ErrorStrategy = ErrorStrategy.STOP,
        llm_client: Optional[Any] = None,
    ):
        self.error_strategy = error_strategy
        self.llm_client = llm_client

    def _create_result(
        self, node_id: str, status: TaskStatus = TaskStatus.PENDING
    ) -> ExecutionResult:
        return ExecutionResult(node_id=node_id, status=status)


class ParallelExecutor(BaseExecutor):
    """Executes tasks in parallel using asyncio.gather."""

    def __init__(
        self,
        max_concurrency: int = 10,
        error_strategy: ErrorStrategy = ErrorStrategy.STOP,
        llm_client: Optional[Any] = None,
    ):
        super().__init__(error_strategy, llm_client)
        self.max_concurrency = max_concurrency

    async def run(
        self,
        graph: ExecutionGraph,
        initial_input: Any = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionStatus:
        """Execute all nodes in the graph in parallel batches."""
        status = ExecutionStatus(
            strategy=ExecutionStrategy.PARALLEL,
            error_strategy=self.error_strategy,
            started_at=time.time(),
        )

        if context is None:
            context = {}
        if initial_input is not None:
            context["input"] = initial_input

        # Validate graph
        errors = graph.validate()
        if errors:
            for err in errors:
                result = ExecutionResult(
                    node_id="__validation__", error=err, status=TaskStatus.FAILED
                )
                status.add_result(result)
            status.completed_at = time.time()
            status.total_duration = status.completed_at - status.started_at
            return status

        # Execute in parallel batches
        try:
            batches = graph.get_parallel_batches()
            for batch in batches:
                await self._execute_batch(batch, graph, status, context)

                # Check for failures and apply error strategy
                if self.error_strategy != ErrorStrategy.CONTINUE:
                    failed = [
                        r
                        for r in status.results.values()
                        if r.status == TaskStatus.FAILED
                    ]
                    if failed:
                        if self.error_strategy == ErrorStrategy.STOP:
                            # Cancel remaining batches
                            break
                        elif self.error_strategy == ErrorStrategy.FAIL_FAST:
                            # Mark remaining as cancelled
                            remaining_nodes = [
                                nid for nid in graph.nodes if nid not in status.results
                            ]
                            for nid in remaining_nodes:
                                result = ExecutionResult(
                                    node_id=nid, status=TaskStatus.CANCELLED
                                )
                                status.add_result(result)
                            break
        except Exception as e:
            result = ExecutionResult(
                node_id="__execution__", error=str(e), status=TaskStatus.FAILED
            )
            status.add_result(result)

        status.completed_at = time.time()
        status.total_duration = status.completed_at - status.started_at
        return status

    async def _execute_batch(
        self,
        node_ids: List[str],
        graph: ExecutionGraph,
        status: ExecutionStatus,
        context: Dict[str, Any],
    ) -> None:
        """Execute a batch of nodes in parallel."""
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def execute_with_semaphore(node_id: str) -> ExecutionResult:
            async with semaphore:
                return await self._execute_node(node_id, graph, context)

        results = await asyncio.gather(
            *[execute_with_semaphore(nid) for nid in node_ids],
            return_exceptions=True,
        )

        for node_id, result in zip(node_ids, results):
            if isinstance(result, Exception):
                result = ExecutionResult(
                    node_id=node_id,
                    error=str(result),
                    status=TaskStatus.FAILED,
                )
            status.add_result(result)

    async def _execute_node(
        self,
        node_id: str,
        graph: ExecutionGraph,
        context: Dict[str, Any],
    ) -> ExecutionResult:
        """Execute a single node."""
        node = graph.get_node(node_id)
        if not node:
            return ExecutionResult(
                node_id=node_id,
                error=f"Node not found: {node_id}",
                status=TaskStatus.FAILED,
            )

        result = ExecutionResult(
            node_id=node_id, status=TaskStatus.RUNNING, started_at=time.time()
        )

        try:
            # Wait for dependencies
            if node.depends_on:
                await self._wait_for_dependencies(node.depends_on, context)

            # Execute handler
            if node.handler:
                handler_result = node.handler(context)
                # Handle both async handlers (coroutine functions) and sync handlers that return coroutines
                if asyncio.iscoroutine(handler_result):
                    if node.timeout:
                        result.output = await asyncio.wait_for(
                            handler_result, timeout=node.timeout
                        )
                    else:
                        result.output = await handler_result
                else:
                    result.output = handler_result
            elif self.llm_client:
                result.output = await self._execute_with_llm(node, context)
            else:
                result.output = None

            result.status = TaskStatus.COMPLETED

        except asyncio.TimeoutError:
            result.error = f"Task timed out after {node.timeout}s"
            result.status = TaskStatus.FAILED
        except Exception as e:
            result.error = str(e)
            result.status = TaskStatus.FAILED

        result.completed_at = time.time()
        result.duration = result.completed_at - result.started_at
        return result

    async def _wait_for_dependencies(
        self,
        depends_on: List[str],
        context: Dict[str, Any],
    ) -> None:
        """Wait for dependent tasks to complete (placeholder - actual impl needs status)."""
        # In a full implementation, this would wait on a shared status object
        pass

    async def _execute_with_llm(self, node: TaskNode, context: Dict[str, Any]) -> str:
        """Execute node using LLM client."""
        if not self.llm_client:
            return ""

        messages = [{"role": "user", "content": node.prompt}]
        return await self.llm_client.achat(messages)


class SerialExecutor(BaseExecutor):
    """Executes tasks sequentially, passing context between steps."""

    async def run(
        self,
        graph: ExecutionGraph,
        initial_input: Any = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionStatus:
        """Execute nodes in topological order."""
        status = ExecutionStatus(
            strategy=ExecutionStrategy.SERIAL,
            error_strategy=self.error_strategy,
            started_at=time.time(),
        )

        if context is None:
            context = {}
        if initial_input is not None:
            context["input"] = initial_input

        # Validate graph
        errors = graph.validate()
        if errors:
            for err in errors:
                result = ExecutionResult(
                    node_id="__validation__", error=err, status=TaskStatus.FAILED
                )
                status.add_result(result)
            status.completed_at = time.time()
            status.total_duration = status.completed_at - status.started_at
            return status

        try:
            execution_order = graph.get_execution_order()
            for node_id in execution_order:
                node = graph.get_node(node_id)
                if not node:
                    continue

                result = await self._execute_node(node, context)
                status.add_result(result)
                context[node_id] = result.output

                # Stop on error if configured
                if (
                    result.status == TaskStatus.FAILED
                    and self.error_strategy == ErrorStrategy.STOP
                ):
                    break

        except Exception as e:
            result = ExecutionResult(
                node_id="__execution__", error=str(e), status=TaskStatus.FAILED
            )
            status.add_result(result)

        status.completed_at = time.time()
        status.total_duration = status.completed_at - status.started_at
        return status

    async def _execute_node(
        self, node: TaskNode, context: Dict[str, Any]
    ) -> ExecutionResult:
        """Execute a single node."""
        result = ExecutionResult(
            node_id=node.id, status=TaskStatus.RUNNING, started_at=time.time()
        )

        try:
            if asyncio.iscoroutinefunction(node.handler) if node.handler else False:
                if node.timeout:
                    result.output = await asyncio.wait_for(
                        node.handler(context), timeout=node.timeout
                    )
                else:
                    result.output = await node.handler(context)
            elif node.handler:
                result.output = node.handler(context)
            elif self.llm_client:
                messages = [{"role": "user", "content": node.prompt}]
                result.output = await self.llm_client.achat(messages)
            else:
                result.output = None

            result.status = TaskStatus.COMPLETED

        except asyncio.TimeoutError:
            result.error = f"Task timed out after {node.timeout}s"
            result.status = TaskStatus.FAILED
        except Exception as e:
            result.error = str(e)
            result.status = TaskStatus.FAILED

        result.completed_at = time.time()
        result.duration = result.completed_at - result.started_at
        return result
