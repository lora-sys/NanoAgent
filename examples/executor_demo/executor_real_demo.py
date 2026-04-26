"""Executor Real API Demo - 测试并行执行器在真实LLM调用下的性能."""

import asyncio
import time
from core.agent import NanoAgent
from core.executor import ParallelExecutor, SerialExecutor, ExecutionGraph, TaskNode
from llm.client import NanoLLMClient


async def demo_parallel_llm_calls():
    """测试并行LLM调用的性能提升."""
    print("\n" + "=" * 60)
    print("Demo: Parallel LLM Calls Performance")
    print("=" * 60)

    llm = NanoLLMClient()

    # 模拟3个独立的分析任务
    async def analyze_code(task_id: str, prompt: str):
        """单个分析任务."""
        start = time.time()
        messages = [{"role": "user", "content": prompt}]
        result = await llm.achat(messages)
        duration = time.time() - start
        return {
            "task_id": task_id,
            "prompt": prompt,
            "result": result[:100] + "..." if len(result) > 100 else result,
            "duration": duration,
        }

    tasks = [
        ("task_1", "Explain what a decorator does in Python in 2 sentences"),
        ("task_2", "Explain what a context manager does in Python in 2 sentences"),
        ("task_3", "Explain what a generator does in Python in 2 sentences"),
    ]

    # Serial execution
    print("\n[Serial Execution]")
    serial_start = time.time()
    serial_results = []
    for task_id, prompt in tasks:
        result = await analyze_code(task_id, prompt)
        serial_results.append(result)
    serial_total = time.time() - serial_start
    print(f"Serial total time: {serial_total:.2f}s")

    # Parallel execution
    print("\n[Parallel Execution]")
    parallel_start = time.time()
    results = await asyncio.gather(
        *[analyze_code(task_id, prompt) for task_id, prompt in tasks]
    )
    parallel_total = time.time() - parallel_start
    print(f"Parallel total time: {parallel_total:.2f}s")

    # Results
    print("\n[Results]")
    for r in results:
        print(f"  {r['task_id']}: {r['duration']:.2f}s")

    speedup = serial_total / parallel_total if parallel_total > 0 else 0
    print(f"\nSpeedup: {speedup:.2f}x")
    print(f"Time saved: {serial_total - parallel_total:.2f}s")


async def demo_agent_with_executor():
    """测试Agent使用executor执行多任务."""
    print("\n" + "=" * 60)
    print("Demo: Agent with Executor - Multi-task Execution")
    print("=" * 60)

    # 创建带executor的Agent
    executor = ParallelExecutor(max_concurrency=3)
    agent = NanoAgent(executor=executor)

    # 多任务查询
    task = "Explain in one sentence each: 1) What is asyncio 2) What is a coroutine 3) What is an event loop"

    print(f"\nTask: {task}")
    print("\nUsing executor mode (detects multiple tasks)...")

    start = time.time()
    result = agent.run(task)
    duration = time.time() - start

    print(f"\nExecution time: {duration:.2f}s")
    print(f"Execution mode: {result.get('execution_mode', 'unknown')}")
    print(f"Status: {result.get('status', 'unknown')}")

    if "response" in result:
        print(f"\nResponse:\n{result['response']}")


async def demo_graph_execution():
    """测试基于图的执行器."""
    print("\n" + "=" * 60)
    print("Demo: Graph-based Task Execution")
    print("=" * 60)

    llm = NanoLLMClient()

    async def llm_task(prompt: str):
        """使用LLM执行任务."""
        messages = [{"role": "user", "content": prompt}]
        return await llm.achat(messages)

    # 构建执行图
    graph = ExecutionGraph(name="analysis_graph")

    # 节点1: 初步分析
    async def analyze_handler(ctx):
        return await llm_task("What are the key benefits of async/await in Python?")

    graph.add_node(TaskNode(
        id="analyze",
        name="Analyze",
        handler=analyze_handler,
    ))

    # 节点2: 详细解释 (依赖节点1)
    async def explain_handler(ctx):
        analyze_result = ctx.get("analyze", "N/A")
        return await llm_task(f"Based on this summary: {analyze_result}, give 3 concrete examples")

    graph.add_node(TaskNode(
        id="explain",
        name="Explain",
        handler=explain_handler,
        depends_on=["analyze"],
    ))

    # 节点3: 代码示例 (依赖节点2)
    async def examples_handler(ctx):
        explain_result = ctx.get("explain", "N/A")
        return await llm_task(f"Based on this explanation: {explain_result}, give 2 code examples demonstrating async/await patterns")

    graph.add_node(TaskNode(
        id="examples",
        name="Examples",
        handler=examples_handler,
        depends_on=["explain"],
    ))

    graph.entry_point = "analyze"

    # 使用串行执行器
    executor = SerialExecutor(llm_client=llm)

    print("\nExecuting graph (serial with dependencies)...")
    start = time.time()
    status = await executor.run(graph)
    duration = time.time() - start

    print(f"\nExecution time: {duration:.2f}s")
    print(f"Total tasks: {len(status.results)}")

    for node_id, result in status.results.items():
        print(f"\n[{node_id}] Status: {result.status.value}")
        if result.output:
            print(f"  Output: {result.output[:150]}..." if len(str(result.output)) > 150 else f"  Output: {result.output}")


async def demo_parallel_independent_tasks():
    """测试完全独立的并行任务."""
    print("\n" + "=" * 60)
    print("Demo: Parallel Independent Tasks")
    print("=" * 60)

    llm = NanoLLMClient()

    async def llm_call(task_id: str, prompt: str):
        """独立的LLM调用."""
        start = time.time()
        messages = [{"role": "user", "content": prompt}]
        result = await llm.achat(messages)
        return {
            "task_id": task_id,
            "duration": time.time() - start,
            "output": result[:80] + "..." if len(result) > 80 else result,
        }

    # 创建完全独立的任务图
    graph = ExecutionGraph(name="parallel_tasks")

    prompts = [
        ("what_is_1", "What is 1+1? Answer in 5 words."),
        ("what_is_2", "What is 2+2? Answer in 5 words."),
        ("what_is_3", "What is 3+3? Answer in 5 words."),
    ]

    for task_id, prompt in prompts:
        graph.add_node(TaskNode(
            id=task_id,
            name=task_id,
            handler=lambda ctx, p=prompt, tid=task_id: llm_call(tid, p),
        ))

    graph.entry_point = "what_is_1"

    # 并行执行
    executor = ParallelExecutor(max_concurrency=3, llm_client=llm)

    print("\nExecuting 3 independent LLM calls in parallel...")
    start = time.time()
    status = await executor.run(graph)
    duration = time.time() - start

    print(f"\nTotal time: {duration:.2f}s")

    for node_id, result in status.results.items():
        print(f"\n[{node_id}] {result.duration:.2f}s")
        print(f"  {result.output}")

    # Serial baseline
    print("\n[Serial Baseline]")
    serial_start = time.time()
    for task_id, prompt in prompts:
        await llm_call(task_id, prompt)
    serial_duration = time.time() - serial_start
    print(f"Serial time: {serial_duration:.2f}s")

    speedup = serial_duration / duration if duration > 0 else 0
    print(f"\nSpeedup: {speedup:.2f}x")


async def main():
    """运行所有demo."""
    print("\n" + "#" * 60)
    print("# NanoAgent Executor Real API Demo")
    print("#" * 60)

    # Demo 1: Parallel LLM calls
    await demo_parallel_llm_calls()

    # Demo 2: Agent with executor
    await demo_agent_with_executor()

    # Demo 3: Graph execution
    await demo_graph_execution()

    # Demo 4: Parallel independent tasks
    await demo_parallel_independent_tasks()

    print("\n" + "#" * 60)
    print("# All Demos Completed!")
    print("#" * 60)


if __name__ == "__main__":
    asyncio.run(main())
