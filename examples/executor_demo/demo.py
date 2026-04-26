"""Executor Module Demo - Parallel, Serial, and Conditional Execution."""

import asyncio
from core.executor import (
    ExecutionGraph,
    TaskNode,
    Condition,
    ParallelExecutor,
    SerialExecutor,
    FlowController,
    ErrorStrategy,
    ExecutionResult,
    TaskStatus,
)


async def demo_parallel_execution():
    """Demo 1: Parallel task execution."""
    print("\n=== Demo 1: Parallel Execution ===")

    async def fetch_data(source: str):
        await asyncio.sleep(0.1)  # Simulate I/O
        return f"Data from {source}"

    graph = ExecutionGraph(name="parallel_demo")
    graph.add_node(TaskNode(id="api", name="API", handler=lambda _: fetch_data("API")))
    graph.add_node(TaskNode(id="db", name="Database", handler=lambda _: fetch_data("Database")))
    graph.add_node(TaskNode(id="cache", name="Cache", handler=lambda _: fetch_data("Cache")))
    graph.entry_point = "api"

    executor = ParallelExecutor(max_concurrency=3)
    status = await executor.run(graph)

    print(f"Completed: {len(status.results)} tasks in {status.total_duration:.2f}s")
    for node_id, result in status.results.items():
        print(f"  {node_id}: {result.output}")


async def demo_serial_execution():
    """Demo 2: Sequential chain execution with context propagation."""
    print("\n=== Demo 2: Serial Chain ===")

    def analyze(text: str):
        return f"Analysis of: {text}"

    def plan(analysis: str):
        return f"Plan based on: {analysis}"

    def execute(plan: str):
        return f"Executing: {plan}"

    graph = ExecutionGraph(name="serial_demo")
    graph.add_node(TaskNode(id="analyze", name="Analyze", handler=lambda ctx: analyze(ctx.get("input", ""))))
    graph.add_node(TaskNode(id="plan", name="Plan", handler=lambda ctx: plan(ctx.get("analyze"))))
    graph.add_node(TaskNode(id="execute", name="Execute", handler=lambda ctx: execute(ctx.get("plan"))))
    graph.entry_point = "analyze"

    # Set up chain dependencies
    graph.get_node("plan").depends_on = ["analyze"]
    graph.get_node("execute").depends_on = ["plan"]

    executor = SerialExecutor()
    status = await executor.run(graph, initial_input="user request")

    print(f"Chain completed: {status.total_duration:.2f}s")
    for node_id, result in status.results.items():
        print(f"  {node_id}: {result.output}")


async def demo_conditional_branching():
    """Demo 3: Conditional branching based on task result."""
    print("\n=== Demo 3: Conditional Branching ===")

    def validate(input: str):
        # Simulate validation
        if "error" in input.lower():
            return {"valid": False, "reason": "Contains error"}
        return {"valid": True, "reason": "OK"}

    def handle_success(ctx):
        return "SUCCESS: Processing completed normally"

    def handle_error(ctx):
        return "ERROR: Handling error case"

    graph = ExecutionGraph(name="conditional_demo")
    graph.add_node(TaskNode(id="validate", name="Validate", handler=lambda ctx: validate(ctx.get("input", ""))))
    graph.add_node(TaskNode(id="success", name="Success", handler=handle_success))
    graph.add_node(TaskNode(id="error", name="Error", handler=handle_error))
    graph.entry_point = "validate"

    # Add condition to validate node
    graph.get_node("validate").conditions = [
        Condition(
            expression='result.get("valid", False) == True',
            then_node="success",
            else_node="error",
        )
    ]
    graph.get_node("success").depends_on = ["validate"]
    graph.get_node("error").depends_on = ["validate"]

    # Execute with FlowController
    controller = FlowController()
    status = await controller.execute_with_flow(graph, initial_input="normal operation")

    print(f"Conditional execution completed: {status.total_duration:.2f}s")
    for node_id, result in status.results.items():
        print(f"  {node_id}: {result.output}")


async def demo_error_strategies():
    """Demo 4: Different error handling strategies."""
    print("\n=== Demo 4: Error Strategies ===")

    def failing_task(_):
        raise ValueError("Simulated failure")

    def other_task(_):
        return "Other task completed"

    for strategy in [ErrorStrategy.STOP, ErrorStrategy.FAIL_FAST, ErrorStrategy.CONTINUE]:
        graph = ExecutionGraph(name=f"strategy_{strategy.value}")
        graph.add_node(TaskNode(id="fail", name="Failing", handler=failing_task))
        graph.add_node(TaskNode(id="other", name="Other", handler=other_task))
        graph.entry_point = "fail"
        graph.get_node("other").depends_on = ["fail"]

        executor = ParallelExecutor(error_strategy=strategy)
        status = await executor.run(graph)

        fail_status = status.results.get("fail", ExecutionResult(node_id="fail", status=TaskStatus.PENDING)).status.value
        other_status = status.results.get("other", ExecutionResult(node_id="other", status=TaskStatus.PENDING)).status.value
        print(f"  {strategy.value}: fail={fail_status}, other={other_status}")


async def main():
    """Run all demos."""
    print("NanoAgent Executor Module Demo")
    print("=" * 50)

    await demo_parallel_execution()
    await demo_serial_execution()
    await demo_conditional_branching()
    await demo_error_strategies()

    print("\n" + "=" * 50)
    print("All demos completed!")


if __name__ == "__main__":
    asyncio.run(main())
