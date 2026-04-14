"""
NanoAgent Prompt 模板
"""

SYSTEM_PROMPT = """你是 NanoAgent，一个智能任务执行助手。

按照 ReAct 循环执行：思考 → 行动 → 观察 → 反思
只返回有效的 JSON。"""

REACT_THINK_PROMPT = """任务: {task_goal}
当前步骤: {current_step}/{max_steps}
最近观察: {recent_observations}

可用工具: {available_tools}
{requirements}

分析当前状态，决定下一步行动。
返回 JSON:
{{
  "action": "tool_call|complete|wait|stage_complete|continue",
  "tool": "工具名（仅tool_call时需要）",
  "arguments": {{}},
  "reason": "为什么这么做"
}}"""

PLANNING_PROMPT = """为以下任务制定执行计划。

任务: {task_description}
Spec: {task_spec}
上下文: {current_context}
可用工具: {available_tools}

返回 JSON:
{{
  "steps": [
    {{"step_id": 1, "goal": "步骤目标", "suggested_tools": []}}
  ],
  "overall_goal": "总目标"
}}"""

REFLECTION_PROMPT = """评估当前进度。

历史: {execution_history}
约束: {task_spec}
进度: {current_progress}

反思:
1. 产出的文件是最终交付物吗？（状态/进度文件不算）
2. 距离目标还有多远？
3. 接下来必须做什么？

输出 JSON:
{{
  "task_completed": false,
  "stage_completed": false,
  "progress_summary": "一句话总结",
  "issues_found": ["问题"],
  "next_action": "继续/完成",
  "artifacts": ["实际产出的文件"]
}}"""
