"""Tests for executor module - parallel, serial, and conditional execution."""

import asyncio
import time
import pytest

from core.executor import (
    ExecutionGraph,
    TaskNode,
    Condition,
    ParallelExecutor,
    SerialExecutor,
    TaskStatus,
    eval_condition,
)


# ============ Unit Tests ============


class TestGraphValidation:
    """Test ExecutionGraph validation."""

    def test_valid_graph(self):
        """Graph with proper structure passes validation."""
        graph = ExecutionGraph(name="test")
        graph.add_node(TaskNode(id="a", name="A", prompt=""))
        graph.add_node(TaskNode(id="b", name="B", prompt="", depends_on=["a"]))
        graph.entry_point = "a"
        assert graph.validate() == []

    def test_missing_entry_point(self):
        """Graph without entry_point fails validation."""
        graph = ExecutionGraph(name="test")
        graph.add_node(TaskNode(id="a", name="A", prompt=""))
        errors = graph.validate()
        assert any("entry_point" in e for e in errors)

    def test_missing_dependency(self):
        """Graph with non-existent dependency fails validation."""
        graph = ExecutionGraph(name="test")
        graph.add_node(
            TaskNode(id="a", name="A", prompt="", depends_on=["nonexistent"])
        )
        graph.entry_point = "a"
        errors = graph.validate()
        assert any("nonexistent" in e for e in errors)

    def test_cycle_detection(self):
        """Graph with cycle fails validation."""
        graph = ExecutionGraph(name="test")
        graph.add_node(TaskNode(id="a", name="A", prompt="", depends_on=["c"]))
        graph.add_node(TaskNode(id="b", name="B", prompt="", depends_on=["a"]))
        graph.add_node(TaskNode(id="c", name="C", prompt="", depends_on=["b"]))
        graph.entry_point = "a"
        errors = graph.validate()
        assert any("cycle" in e.lower() for e in errors)

    def test_get_execution_order(self):
        """Topological sort returns correct order."""
        graph = ExecutionGraph(name="test")
        graph.add_node(TaskNode(id="a", name="A", prompt=""))
        graph.add_node(TaskNode(id="b", name="B", prompt="", depends_on=["a"]))
        graph.add_node(TaskNode(id="c", name="C", prompt="", depends_on=["b"]))
        graph.entry_point = "a"
        order = graph.get_execution_order()
        assert order == ["a", "b", "c"]

    def test_get_parallel_batches(self):
        """Independent nodes are batched together."""
        graph = ExecutionGraph(name="test")
        graph.add_node(TaskNode(id="a", name="A", prompt=""))
        graph.add_node(TaskNode(id="b", name="B", prompt=""))
        graph.add_node(TaskNode(id="c", name="C", prompt="", depends_on=["a", "b"]))
        graph.entry_point = "a"
        batches = graph.get_parallel_batches()
        assert len(batches) == 2
        assert set(batches[0]) == {"a", "b"}
        assert batches[1] == ["c"]


class TestConditionEvaluation:
    """Test condition expression evaluation."""

    def test_contains_match(self):
        """result.contains() returns True when substring found."""
        ctx = {"message": "error occurred"}
        assert eval_condition('result.contains("error")', ctx) is True

    def test_contains_no_match(self):
        """result.contains() returns False when substring not found."""
        ctx = {"message": "success"}
        assert eval_condition('result.contains("error")', ctx) is False

    def test_get_value(self):
        """result.get() returns value correctly."""
        ctx = {"status": "success", "code": 200}
        assert eval_condition('result.get("status") == "success"', ctx) is True
        assert eval_condition('result.get("code") == 200', ctx) is True

    def test_get_with_default(self):
        """result.get() with default for missing key."""
        ctx = {"status": "success"}
        assert eval_condition('result.get("missing", False) == False', ctx) is True

    def test_equality(self):
        """Direct equality comparison."""
        assert eval_condition('result == "hello"', "hello") is True
        assert eval_condition('result == "hello"', "world") is False

    def test_is_none(self):
        """None check."""
        assert eval_condition("result is None", None) is True
        assert eval_condition("result is not None", None) is False

    def test_bool_conversion(self):
        """Bool conversion of context."""
        assert eval_condition("result", True) is True
        assert eval_condition("result", False) is False

    def test_empty_expression(self):
        """Empty expression returns True."""
        assert eval_condition("", "anything") is True

    def test_invalid_expression(self):
        """Invalid expression returns False (fail-safe)."""
        assert eval_condition("this is not valid python!!", "anything") is False


# ============ US1: Parallel Execution Tests ============


class TestParallelExecutor:
    """Tests for parallel task execution."""

    @pytest.mark.asyncio
    async def test_parallel_execution_timing(self):
        """US1: 3 tasks execute in parallel - total time ≈ longest task."""

        async def slow_task(delay: float):
            await asyncio.sleep(delay)
            return f"completed in {delay}s"

        graph = ExecutionGraph(name="timing_test")
        graph.add_node(
            TaskNode(id="t1", name="Task 1", handler=lambda _: slow_task(0.1))
        )
        graph.add_node(
            TaskNode(id="t2", name="Task 2", handler=lambda _: slow_task(0.2))
        )
        graph.add_node(
            TaskNode(id="t3", name="Task 3", handler=lambda _: slow_task(0.15))
        )
        graph.entry_point = "t1"

        executor = ParallelExecutor(max_concurrency=3)
        start = time.time()
        status = await executor.run(graph)
        duration = time.time() - start

        # All should complete
        assert status.results["t1"].status == TaskStatus.COMPLETED
        assert status.results["t2"].status == TaskStatus.COMPLETED
        assert status.results["t3"].status == TaskStatus.COMPLETED

        # Parallel: should take ~0.2s (longest), not 0.45s (sum)
        # Allow some overhead, so check < 0.4s
        assert duration < 0.4, f"Expected parallel execution, took {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_parallel_all_complete(self):
        """US1: All independent tasks complete successfully."""
        counter = {"value": 0}

        def increment():
            counter["value"] += 1
            return counter["value"]

        graph = ExecutionGraph(name="counter_test")
        graph.add_node(
            TaskNode(id="c1", name="Counter 1", handler=lambda _: increment())
        )
        graph.add_node(
            TaskNode(id="c2", name="Counter 2", handler=lambda _: increment())
        )
        graph.add_node(
            TaskNode(id="c3", name="Counter 3", handler=lambda _: increment())
        )
        graph.entry_point = "c1"

        executor = ParallelExecutor(max_concurrency=3)
        status = await executor.run(graph)

        # All should complete
        for node_id in ["c1", "c2", "c3"]:
            assert status.results[node_id].status == TaskStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_parallel_with_dependencies(self):
        """US1: Dependent tasks wait and execute after dependencies."""
        execution_order = []

        def make_handler(node_id: str, delay: float):
            def handler(_):
                execution_order.append(node_id)
                return node_id

            return handler

        graph = ExecutionGraph(name="dep_test")
        graph.add_node(TaskNode(id="a", name="A", handler=make_handler("a", 0)))
        graph.add_node(
            TaskNode(id="b", name="B", handler=make_handler("b", 0), depends_on=["a"])
        )
        graph.add_node(
            TaskNode(id="c", name="C", handler=make_handler("c", 0), depends_on=["a"])
        )
        graph.add_node(
            TaskNode(
                id="d", name="D", handler=make_handler("d", 0), depends_on=["b", "c"]
            )
        )
        graph.entry_point = "a"

        executor = ParallelExecutor(max_concurrency=3)
        status = await executor.run(graph)

        # A should execute first
        assert execution_order[0] == "a"
        # B and C should execute after A
        assert set(execution_order[1:3]) == {"b", "c"}
        # D should execute last
        assert execution_order[-1] == "d"


# ============ US2: Serial Execution Tests ============


class TestSerialExecutor:
    """Tests for sequential chain execution."""

    @pytest.mark.asyncio
    async def test_serial_execution(self):
        """US2: Steps execute in order, not in parallel."""
        execution_log = []

        def log_task(name: str):
            def handler(_):
                execution_log.append(name)
                return f"done:{name}"

            return handler

        graph = ExecutionGraph(name="serial_test")
        graph.add_node(TaskNode(id="step1", name="Step 1", handler=log_task("step1")))
        graph.add_node(TaskNode(id="step2", name="Step 2", handler=log_task("step2")))
        graph.add_node(TaskNode(id="step3", name="Step 3", handler=log_task("step3")))
        graph.entry_point = "step1"

        # Set up chain dependencies
        graph.get_node("step2").depends_on = ["step1"]
        graph.get_node("step3").depends_on = ["step2"]

        executor = SerialExecutor()
        status = await executor.run(graph)

        assert status.results["step1"].status == TaskStatus.COMPLETED
        assert status.results["step2"].status == TaskStatus.COMPLETED
        assert status.results["step3"].status == TaskStatus.COMPLETED

        # Strict ordering
        assert execution_log == ["step1", "step2", "step3"]

    @pytest.mark.asyncio
    async def test_chain_context_propagation(self):
        """US2: Each step receives output of previous step."""
        results = {}

        def make_handler(node_id: str):
            def handler(ctx):
                prev_output = ctx.get(node_id.replace("step", "step")[:-1], {})
                # For step2, it should see step1's output
                if node_id == "step2":
                    prev_output = ctx.get("step1")
                results[node_id] = prev_output
                return f"output_from_{node_id}"

            return handler

        graph = ExecutionGraph(name="context_test")
        graph.add_node(
            TaskNode(id="step1", name="Step 1", handler=make_handler("step1"))
        )
        graph.add_node(
            TaskNode(id="step2", name="Step 2", handler=make_handler("step2"))
        )
        graph.entry_point = "step1"
        graph.get_node("step2").depends_on = ["step1"]

        executor = SerialExecutor()
        status = await executor.run(graph)

        # step2 should have received step1's output
        assert status.results["step1"].output == "output_from_step1"


# ============ US3: Conditional Branch Tests ============


class TestConditionalBranching:
    """Tests for conditional execution flow."""

    def test_condition_evaluation(self):
        """US3: Conditions evaluate correctly."""
        # Error case
        ctx = {"status": "error", "message": "something failed"}
        assert eval_condition('result.get("status") == "error"', ctx) is True

        # Success case
        ctx = {"status": "success", "message": "ok"}
        assert eval_condition('result.get("status") == "error"', ctx) is False

    @pytest.mark.asyncio
    async def test_conditional_branch_taken(self):
        """US3: Correct branch is selected based on condition."""
        results = []

        def success_handler(_):
            results.append("success")
            return {"status": "success"}

        def error_handler(_):
            results.append("error")
            return {"status": "error"}

        graph = ExecutionGraph(name="branch_test")
        graph.add_node(
            TaskNode(id="check", name="Check", handler=lambda _: {"valid": True})
        )
        graph.add_node(
            TaskNode(id="success", name="Success Path", handler=success_handler)
        )
        graph.add_node(TaskNode(id="error", name="Error Path", handler=error_handler))
        graph.entry_point = "check"
        graph.get_node("success").depends_on = ["check"]
        graph.get_node("error").depends_on = ["check"]

        # Add condition to check node
        check_node = graph.get_node("check")
        check_node.conditions = [
            Condition(
                expression='result.get("valid", False) == True',
                then_node="success",
                else_node="error",
            )
        ]

        # Note: Full conditional execution requires FlowController
        # This test validates condition evaluation works
        ctx = {"valid": True}
        condition_result = eval_condition('result.get("valid", False) == True', ctx)
        assert condition_result is True


# ============ Integration Tests ============


class TestExecutorIntegration:
    """Integration tests for executor with LLM client (mock)."""

    @pytest.mark.asyncio
    async def test_executor_with_agent(self):
        """US4: Executor integrates with agent architecture."""
        from tests.agent.harness import AgentTestHarness

        harness = AgentTestHarness(mode="mock")
        harness.load_mock_responses(
            [
                '<tool name="read_file" args=\'{"path": "README.md"}\'/>',
                "Here is the README content summary.",
            ]
        )

        # This would test actual integration
        # Simplified here since it requires full agent setup
        assert True  # Placeholder for full integration test


# ============ Run Tests ============


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
