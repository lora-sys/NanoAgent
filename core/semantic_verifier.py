"""语义验证器 - 简化版本

遵循 AGENT.md 原则：
- clean + zero magic
- more use builtin function
- keep it code readable and clean
"""

import re
from typing import Any, List, Set, Dict
from dataclasses import dataclass
from enum import Enum


class MatchType(Enum):
    """匹配类型"""

    EXACT = "exact"
    CONTAINS = "contains"
    SEMANTIC = "semantic"


@dataclass
class MatchResult:
    """匹配结果"""

    matched: bool
    confidence: float
    details: str


class SemanticVerifier:
    """简化的语义验证器"""

    def __init__(self):
        self.stop_words = {
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "need",
            "dare",
            "的",
            "了",
            "是",
            "在",
            "有",
            "和",
            "与",
            "或",
            "但",
            "而",
            "及",
            "等",
            "很",
            "也",
            "都",
            "就",
            "还",
            "又",
            "这",
            "那",
            "些",
            "此",
        }

    def verify(
        self, expected: Any, actual: str, match_type: MatchType = MatchType.SEMANTIC
    ) -> MatchResult:
        """验证匹配"""
        if match_type == MatchType.EXACT:
            return self._exact_match(expected, actual)
        elif match_type == MatchType.CONTAINS:
            return self._contains_match(expected, actual)
        else:
            return self._semantic_match(expected, actual)

    def _exact_match(self, expected: Any, actual: str) -> MatchResult:
        """精确匹配"""
        expected_str = str(expected).strip()
        actual_str = actual.strip()
        matched = expected_str == actual_str
        return MatchResult(
            matched, 1.0 if matched else 0.0, "Exact match" if matched else "No match"
        )

    def _contains_match(self, expected: Any, actual: str) -> MatchResult:
        """包含匹配"""
        actual_lower = actual.lower()

        if isinstance(expected, str):
            items = [expected.lower()]
        elif isinstance(expected, list):
            items = [item.lower() for item in expected]
        else:
            items = [str(expected).lower()]

        matched_count = sum(1 for item in items if item in actual_lower)
        confidence = matched_count / len(items) if items else 1.0

        return MatchResult(
            confidence > 0, confidence, f"Matched {matched_count}/{len(items)} items"
        )

    def _semantic_match(self, expected: Any, actual: str) -> MatchResult:
        """语义匹配"""
        # 提取关键词
        expected_keywords = self._extract_keywords(str(expected))
        actual_keywords = self._extract_keywords(actual)

        if not expected_keywords:
            return MatchResult(True, 1.0, "No keywords to match")

        # 计算匹配度
        matched = expected_keywords & actual_keywords
        confidence = len(matched) / len(expected_keywords)

        # 提取实体进行额外加分
        expected_entities = self._extract_entities(str(expected))
        actual_entities = self._extract_entities(actual)

        entity_bonus = 0.0
        for entity_type in expected_entities:
            if entity_type in actual_entities:
                matches = set(expected_entities[entity_type]) & set(
                    actual_entities[entity_type]
                )
                if matches:
                    entity_bonus += 0.1 * (
                        len(matches) / len(expected_entities[entity_type])
                    )

        final_confidence = min(1.0, confidence + entity_bonus)

        return MatchResult(
            final_confidence >= 0.7,
            final_confidence,
            f"Keyword match: {confidence:.2f}, Entity bonus: {entity_bonus:.2f}",
        )

    def _extract_keywords(self, text: str) -> Set[str]:
        """提取关键词"""
        # 移除特殊字符
        cleaned = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)
        # 提取词汇
        words = re.findall(r"[\w]+|[\u4e00-\u9fff]+", cleaned.lower())
        # 过滤停用词和短词
        return {w for w in words if len(w) >= 2 and w not in self.stop_words}

    def _extract_entities(self, text: str) -> Dict[str, List[str]]:
        """提取实体"""
        return {
            "files": re.findall(r"[\w]+\.(py|js|ts|json|md|txt|yaml|yml|toml)", text),
            "paths": re.findall(r"[/\\][/\\w/\\.-]+", text),
            "numbers": re.findall(r"\d+\.?\d*", text),
        }

    def verify_tool_sequence(
        self, expected: List[str], actual: List[str]
    ) -> MatchResult:
        """验证工具序列"""
        if not expected:
            return MatchResult(True, 1.0, "No expected tools")

        expected_set = set(expected)
        actual_set = set(actual)

        matched = expected_set & actual_set
        set_confidence = len(matched) / len(expected)

        # 检查顺序
        sequence_score = 0.0
        if expected and actual:
            idx = 0
            for tool in actual:
                if idx < len(expected) and tool == expected[idx]:
                    idx += 1
            sequence_score = idx / len(expected)

        final_confidence = set_confidence * 0.7 + sequence_score * 0.3

        return MatchResult(
            final_confidence >= 0.7,
            final_confidence,
            f"Set: {set_confidence:.2f}, Sequence: {sequence_score:.2f}",
        )


def create_verifier() -> SemanticVerifier:
    """创建验证器"""
    return SemanticVerifier()
