"""规划工具 - 将复杂目标分解为结构化执行步骤"""

import json
import uuid
from typing import Any, Dict, List, Optional


PLANNER_PROMPT = """你是一个任务规划专家。你的职责是将复杂目标分解为清晰、可执行的步骤。

## 输入信息
目标: {goal}

{current_state}
{constraints}

## 分解要求
1. 将目标分解为 3-8 个具体、可执行的步骤
2. 每个步骤应该能通过单次工具调用或少量操作完成
3. 考虑步骤之间的依赖关系和执行顺序
4. 识别关键决策点和可能的备选方案
5. 评估每个步骤的复杂度（低/中/高）

## 输出格式
请严格以 JSON 格式返回计划，不要包含任何其他文字：

{{
  "steps": [
    {{
      "step": 1,
      "description": "步骤的清晰描述",
      "reasoning": "为什么需要这个步骤",
      "complexity": "低/中/高",
      "alternative": "如果此步骤失败时的备选方案（可选）"
    }}
  ],
  "total_steps": N,
  "reasoning": "整体规划思路，解释为什么按此顺序执行",
  "estimated_difficulty": "整体难度评估",
  "potential_risks": ["风险1", "风险2（可选）"]
}}

## 示例
目标: "为项目添加用户认证功能"
输出:
{{
  "steps": [
    {{
      "step": 1,
      "description": "分析现有代码结构，找到认证相关的现有代码",
      "reasoning": "需要先了解项目架构，避免重复造轮子",
      "complexity": "低",
      "alternative": null
    }},
    {{
      "step": 2,
      "description": "设计用户数据模型和认证流程",
      "reasoning": "需要先确定数据结构和认证机制",
      "complexity": "中",
      "alternative": "使用现成的认证库如 Authlib"
    }},
    {{
      "step": 3,
      "description": "实现登录/注册 API 端点",
      "reasoning": "核心功能，需要先完成",
      "complexity": "中",
      "alternative": null
    }},
    {{
      "step": 4,
      "description": "添加会话管理和 JWT token",
      "reasoning": "无状态认证，便于扩展",
      "complexity": "中",
      "alternative": "使用 session-based 认证"
    }},
    {{
      "step": 5,
      "description": "编写单元测试覆盖认证流程",
      "reasoning": "确保关键功能正确",
      "complexity": "低",
      "alternative": null
    }}
  ],
  "total_steps": 5,
  "reasoning": "遵循先分析、后设计、再实现的顺序，确保架构合理",
  "estimated_difficulty": "中",
  "potential_risks": ["第三方认证库的依赖版本问题"]
}}

现在开始分解你的目标。直接输出 JSON，不要有其他文字。"""


def plan(
    goal: str,
    current_state: Optional[Dict[str, Any]] = None,
    constraints: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Decomposes a complex goal into structured execution steps.

    Args:
        goal: The high-level goal to decompose into actionable steps
        current_state: Current context (e.g., files modified, completed steps, environment info)
        constraints: List of constraints or requirements (e.g., "must use async", "max 5 steps")

    Returns:
        Dict containing the structured plan with steps, reasoning, and metadata
    """
    # 构建提示词
    if current_state:
        state_lines = "当前状态:\n" + "\n".join(
            f"- {k}: {v}" for k, v in current_state.items()
        )
    else:
        state_lines = "当前状态: 无（从头开始）"

    if constraints:
        constraint_lines = "约束条件:\n" + "\n".join(f"- {c}" for c in constraints)
    else:
        constraint_lines = "约束条件: 无"

    prompt = PLANNER_PROMPT.format(
        goal=goal,
        current_state=state_lines,
        constraints=constraint_lines,
    )

    # 调用 LLM 生成计划
    try:
        from llm.client import NanoLLMClient

        llm = NanoLLMClient()
        response = llm.chat([{"role": "user", "content": prompt}])
    except Exception as e:
        return {
            "error": f"LLM 调用失败: {e}",
            "steps": [],
            "total_steps": 0,
            "plan_id": str(uuid.uuid4())[:8],
        }

    # 解析 LLM 返回的 JSON
    plan_id = str(uuid.uuid4())[:8]
    try:
        # 尝试从响应中提取 JSON
        result = _extract_json(response)
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


def _extract_json(text: str) -> Dict[str, Any]:
    """从文本中提取 JSON 对象"""
    # 尝试直接解析
    text = text.strip()

    # 查找 JSON 对象的起始和结束
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        json_str = text[start : end + 1]
        return json.loads(json_str)

    raise ValueError("No JSON object found in response")
