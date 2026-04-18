"""Shared utilities"""

import json
import re


def extract_json(text: str) -> dict:
    """Extract JSON object from text, handling markdown code blocks and plain JSON.

    Finds the first {...} block or JSON inside ```json ``` fences.
    """
    # 提取 markdown 代码块中的 JSON
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if match:
        text = match.group(1).strip()

    # 查找 JSON 对象的起始和结束位置
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])

    return json.loads(text)
