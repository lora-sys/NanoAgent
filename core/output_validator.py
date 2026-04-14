"""
输出验证器 - NanoAgent

简化版：提取 JSON + Pydantic 验证
"""

import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel
from loguru import logger

T = TypeVar("T", bound=BaseModel)


def validate_output(raw_output: str, response_model: Type[T]) -> T:
    """
    验证 LLM 输出

    Args:
        raw_output: LLM 原始输出
        response_model: 目标 Pydantic 模型

    Returns:
        验证后的 Pydantic 模型实例
    """
    try:
        # 提取 JSON 代码块
        cleaned = _extract_json_block(raw_output)
        data = json.loads(cleaned)

        # 解包嵌套结构 (如 {"TaskSpec": {...}})
        data = _unwrap_nested(data, response_model.__name__)

        return response_model.model_validate(data)
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {e}")
        raise ValueError(f"无法解析 JSON: {e}")
    except Exception as e:
        logger.error(f"验证失败: {e}")
        raise ValueError(f"验证失败: {e}")


def _extract_json_block(raw_output: str) -> str:
    """提取 JSON 代码块"""
    # 尝试 ```json 代码块
    match = re.search(r"```json\s*([\s\S]*?)\s*```", raw_output)
    if match:
        return match.group(1).strip()

    # 尝试 ``` 代码块
    match = re.search(r"```\s*([\s\S]*?)\s*```", raw_output)
    if match:
        extracted = match.group(1).strip()
        if extracted.startswith("{") or extracted.startswith("["):
            return extracted

    # 查找 { ... }
    start = raw_output.find("{")
    end = raw_output.rfind("}")
    if start != -1 and end > start:
        return raw_output[start : end + 1]

    return raw_output


def _unwrap_nested(data: dict, model_name: str) -> dict:
    """解包嵌套的 JSON 结构"""
    if not isinstance(data, dict):
        return data

    keys = list(data.keys())
    if len(keys) == 1 and isinstance(data[keys[0]], dict):
        key = keys[0]
        if key == model_name or model_name.lower() in key.lower():
            return data[key]

    return data
