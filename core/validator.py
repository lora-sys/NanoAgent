"""输出验证器 - JSON 提取 + Pydantic 验证"""

import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def validate_output(raw_output: str, response_model: Type[T]) -> T:
    cleaned = _extract_json(raw_output)
    data = json.loads(cleaned)
    if isinstance(data, dict) and len(data) == 1:
        key = list(data.keys())[0]
        model_name = response_model.__name__
        if key == model_name or model_name.lower() in key.lower():
            data = data[key]
    return response_model.model_validate(data)


def _extract_json(text: str) -> str:
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        extracted = m.group(1).strip()
        if extracted.startswith("{") or extracted.startswith("["):
            return extracted
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return text[start:end + 1]
    return text
