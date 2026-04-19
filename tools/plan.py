"""规划工具 - 将复杂目标分解为结构化执行步骤"""

import asyncio
import uuid
from typing import Any, Dict, List, Optional

from core.utils import extract_json

# 模块级 LLM client，复用避免每次调用重新初始化
_llm_client: Optional[Any] = None


def _get_llm() -> Any:
    """获取复用的 LLM client"""
    global _llm_client
    if _llm_client is None:
        from llm.client import NanoLLMClient

        _llm_client = NanoLLMClient()
    return _llm_client


PLANNER_PROMPT = """将目标分解为 3-8 个可执行步骤。

目标: {goal}
{current_state}{constraints}

输出严格 JSON 格式:
{{
  "steps": [
    {{
      "step": 1,
      "description": "步骤描述",
      "reasoning": "为什么需要此步骤",
      "complexity": "低/中/高",
      "alternative": "失败时的备选方案（可选）"
    }}
  ],
  "total_steps": N,
  "reasoning": "整体规划思路",
  "estimated_difficulty": "低/中/高",
  "potential_risks": ["风险列表（可选）"]
}}

直接输出 JSON，不要有其他文字。"""


def _validate_and_build_prompt(
    goal: str,
    current_state: Optional[Dict[str, Any]],
    constraints: Optional[List[str]],
) -> tuple[str, str]:
    """验证输入并构建提示词，返回 (prompt, plan_id)"""
    plan_id = str(uuid.uuid4())[:8]

    if not goal or not goal.strip():
        return "", plan_id

    state_str = (
        "\n当前状态: " + ", ".join(f"{k}={v}" for k, v in current_state.items())
        if current_state
        else ""
    )
    const_str = (
        "\n约束: " + ", ".join(f"{c}" for c in constraints) if constraints else ""
    )

    prompt = PLANNER_PROMPT.format(
        goal=goal,
        current_state=state_str,
        constraints=const_str,
    )
    return prompt, plan_id


async def aplan(
    goal: str,
    current_state: Optional[Dict[str, Any]] = None,
    constraints: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Decomposes a complex goal into structured execution steps.

    Args:
        goal: The high-level goal to decompose
        current_state: Current context (e.g., files modified, completed steps)
        constraints: List of constraints (e.g., "must use async", "max 5 steps")

    Returns:
        Dict with steps, reasoning, and metadata
    """
    # 输入验证
    if not isinstance(goal, str) or not goal.strip():
        return {
            "error": "goal cannot be empty",
            "steps": [],
            "total_steps": 0,
            "plan_id": str(uuid.uuid4())[:8],
        }
    if current_state is not None and not isinstance(current_state, dict):
        return {
            "error": "current_state must be a dict",
            "steps": [],
            "total_steps": 0,
            "plan_id": str(uuid.uuid4())[:8],
        }
    if constraints is not None and not isinstance(constraints, list):
        return {
            "error": "constraints must be a list",
            "steps": [],
            "total_steps": 0,
            "plan_id": str(uuid.uuid4())[:8],
        }

    prompt, plan_id = _validate_and_build_prompt(goal, current_state, constraints)

    try:
        response = await _get_llm().achat([{"role": "user", "content": prompt}])
    except Exception as e:
        return {
            "error": f"LLM 调用失败: {e}",
            "steps": [],
            "total_steps": 0,
            "plan_id": plan_id,
        }

    try:
        result = extract_json(response)
        if "steps" not in result or not isinstance(result.get("steps"), list):
            result["steps"] = []
        result["total_steps"] = len(result["steps"])
        result["plan_id"] = plan_id
        return result
    except Exception as e:
        return {
            "error": f"解析计划失败: {e}",
            "raw_response": response[:500],
            "steps": [],
            "total_steps": 0,
            "plan_id": plan_id,
        }


def plan(
    goal: str,
    current_state: Optional[Dict[str, Any]] = None,
    constraints: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """同步版本，委托给 async 版本"""
    return asyncio.run(aplan(goal, current_state, constraints))
