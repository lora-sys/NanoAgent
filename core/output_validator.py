"""
输出验证器 - NanoAgent
多层防御的 LLM 输出验证和修复
"""

import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel
from loguru import logger

T = TypeVar("T", bound=BaseModel)


class OutputValidator:
    """多层防御的输出验证器

    Layer 1: Prompt Engineering（基础层）
    Layer 2: JSON Mode（增强层，如果支持）
    Layer 3: 验证 + 修复（保证层）
    Layer 4: 重试机制（最终保证）
    """

    def __init__(self, response_model: Type[T]):
        """
        初始化验证器

        Args:
            response_model: 目标 Pydantic 模型类型
        """
        self.response_model = response_model
        self.model_name = response_model.__name__

    def validate_and_fix(self, raw_output: str) -> T:
        """
        验证并修复输出

        Args:
            raw_output: LLM 原始输出

        Returns:
            验证后的 Pydantic 模型实例

        Raises:
            ValueError: 如果无法修复输出
        """
        try:
            # Layer 1: 提取 JSON 代码块
            cleaned_output = self._extract_json_block(raw_output)

            # Layer 2: 解析 JSON
            data = json.loads(cleaned_output)

            # Layer 3: 处理嵌套结构
            data = self._unwrap_nested(data)

            # Layer 4: 自动修复常见问题
            data = self._auto_fix_common_issues(data)

            # Layer 5: Pydantic 验证
            return self.response_model.model_validate(data)

        except json.JSONDecodeError as e:
            logger.error(f"JSON 解析失败: {e}")
            logger.error(f"原始输出: {raw_output[:500]}...")
            raise ValueError(f"无法解析 JSON: {e}")
        except Exception as e:
            logger.error(f"验证失败: {e}")
            logger.error(f"数据: {data}")
            raise ValueError(f"验证失败: {e}")

    def _extract_json_block(self, raw_output: str) -> str:
        """
        从输出中提取 JSON 代码块

        Args:
            raw_output: 原始输出

        Returns:
            提取的 JSON 字符串
        """
        # 尝试提取 ```json 代码块
        json_pattern = r"```json\s*([\s\S]*?)\s*```"
        match = re.search(json_pattern, raw_output)
        if match:
            extracted = match.group(1).strip()
            logger.info("✓ 从 ```json 代码块中提取 JSON")
            return extracted

        # 尝试提取 ``` 代码块
        code_pattern = r"```\s*([\s\S]*?)\s*```"
        match = re.search(code_pattern, raw_output)
        if match:
            extracted = match.group(1).strip()
            # 检查是否是 JSON
            if extracted.startswith("{") or extracted.startswith("["):
                logger.info("✓ 从 ``` 代码块中提取 JSON")
                return extracted

        # 尝试查找第一个 { 和最后一个 }
        start = raw_output.find("{")
        end = raw_output.rfind("}")
        if start != -1 and end != -1 and end > start:
            extracted = raw_output[start : end + 1]
            logger.info("✓ 从文本中提取 JSON")
            return extracted

        # 如果都没找到，返回原始输出
        logger.warning("⚠️ 无法提取 JSON 代码块，使用原始输出")
        return raw_output

    def _unwrap_nested(self, data: dict) -> dict:
        """
        解包嵌套的 JSON 结构

        Args:
            data: JSON 数据

        Returns:
            解包后的数据
        """
        if not isinstance(data, dict):
            return data

        keys = list(data.keys())

        # 如果只有一个键，且值是字典，尝试解包
        if len(keys) == 1 and isinstance(data[keys[0]], dict):
            key = keys[0]
            # 检查键名是否匹配模型名称
            if key == self.model_name or self.model_name.lower() in key.lower():
                logger.info(f"✓ 解包嵌套结构: {key}")
                return data[key]

        return data

    def _auto_fix_common_issues(self, data: dict) -> dict:
        """
        自动修复常见问题

        Args:
            data: JSON 数据

        Returns:
            修复后的数据
        """
        if not isinstance(data, dict):
            return data

        # 修复 1: boundaries 字段的嵌套结构
        if "boundaries" in data and isinstance(data["boundaries"], dict):
            boundaries = data["boundaries"]
            standard_keys = {"always", "ask_first", "never"}

            if not standard_keys.issubset(boundaries.keys()):
                # 如果没有标准键，但只有一个键，可能是嵌套结构
                if len(boundaries) == 1 and isinstance(
                    list(boundaries.values())[0], dict
                ):
                    nested_boundaries = list(boundaries.values())[0]
                    if standard_keys.issubset(nested_boundaries.keys()):
                        logger.info("✓ 自动修复 boundaries 嵌套结构")
                        data["boundaries"] = nested_boundaries

        # 修复 2: progress_tracking 字段的类型
        if "progress_tracking" in data and isinstance(data["progress_tracking"], list):
            logger.info("✓ 自动修复 progress_tracking 从 list 到 dict")
            data["progress_tracking"] = {
                "current_progress": "进行中",
                "completed_steps": [],
                "remaining": data["progress_tracking"],
            }

        # 修复 3: 确保列表字段是列表
        list_fields = [
            "success_criteria",
            "completed_steps",
            "remaining",
            "always",
            "ask_first",
            "never",
            "self_check_instructions",
            "process_requirements",
        ]

        for field in list_fields:
            if field in data and not isinstance(data[field], list):
                logger.warning(f"⚠️ 字段 {field} 不是列表，尝试转换")
                if isinstance(data[field], str):
                    data[field] = [data[field]]
                else:
                    data[field] = []

        return data


def validate_with_retry(
    raw_output: str,
    response_model: Type[T],
    max_retries: int = 3,
) -> T:
    """
    带重试的验证函数

    Args:
        raw_output: LLM 原始输出
        response_model: 目标 Pydantic 模型类型
        max_retries: 最大重试次数

    Returns:
        验证后的 Pydantic 模型实例

    Raises:
        ValueError: 如果重试后仍然失败
    """
    validator = OutputValidator(response_model)

    for attempt in range(max_retries):
        try:
            return validator.validate_and_fix(raw_output)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"验证失败，已重试 {max_retries} 次: {e}")
                raise
            logger.warning(f"验证失败，尝试 {attempt + 1}/{max_retries}: {e}")

    # 理论上不会到达这里
    raise ValueError("验证失败")
