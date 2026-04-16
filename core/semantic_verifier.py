"""语义验证器 - 实现更精确的语义验证

遵循 AGENT.md 原则：
- 提供更精确的结果验证
- 支持语义级别的匹配
- 提高验证的准确性
"""

import re
import json
from typing import Any, Dict, List, Set
from dataclasses import dataclass
from enum import Enum


class SemanticMatchType(Enum):
    """语义匹配类型"""

    EXACT = "exact"
    CONTAINS = "contains"
    SEMANTIC_SIMILAR = "semantic"
    STRUCTURAL = "structural"
    KEYWORD_BASED = "keyword"
    PATTERN_BASED = "pattern"


@dataclass
class SemanticMatchResult:
    """语义匹配结果"""

    match_type: SemanticMatchType
    confidence: float
    matched_elements: List[str]
    missing_elements: List[str]
    extra_elements: List[str]
    details: Dict[str, Any]

    def is_match(self, threshold: float = 0.7) -> bool:
        """判断是否匹配"""
        return self.confidence >= threshold


class KeywordExtractor:
    """关键词提取器"""

    @staticmethod
    def extract_keywords(text: str, min_length: int = 2) -> Set[str]:
        """提取文本中的关键词"""
        cleaned = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)
        words = re.findall(r"[\w]+|[\u4e00-\u9fff]+", cleaned.lower())

        stop_words = {
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

        keywords = {
            word for word in words if len(word) >= min_length and word not in stop_words
        }

        return keywords

    @staticmethod
    def extract_named_entities(text: str) -> Dict[str, List[str]]:
        """提取命名实体（简化版本）"""
        entities = {
            "files": re.findall(r"[\w]+\.(py|js|ts|json|md|txt|yaml|yml|toml)", text),
            "paths": re.findall(r"[/\\][\w/\\.-]+", text),
            "numbers": re.findall(r"\d+\.?\d*", text),
        }

        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities


class SemanticVerifier:
    """语义验证器"""

    def __init__(self):
        """初始化验证器"""
        self.keyword_extractor = KeywordExtractor()
        self.match_history: List[Dict[str, Any]] = []

    def verify_semantic_match(
        self,
        expected: Any,
        actual: str,
        match_type: SemanticMatchType = SemanticMatchType.SEMANTIC_SIMILAR,
    ) -> SemanticMatchResult:
        """验证语义匹配"""
        if match_type == SemanticMatchType.EXACT:
            return self._verify_exact_match(expected, actual)
        elif match_type == SemanticMatchType.CONTAINS:
            return self._verify_contains_match(expected, actual)
        elif match_type == SemanticMatchType.SEMANTIC_SIMILAR:
            return self._verify_semantic_similarity(expected, actual)
        elif match_type == SemanticMatchType.STRUCTURAL:
            return self._verify_structural_match(expected, actual)
        elif match_type == SemanticMatchType.KEYWORD_BASED:
            return self._verify_keyword_match(expected, actual)
        elif match_type == SemanticMatchType.PATTERN_BASED:
            return self._verify_pattern_match(expected, actual)
        else:
            return SemanticMatchResult(
                match_type=match_type,
                confidence=0.0,
                matched_elements=[],
                missing_elements=[],
                extra_elements=[],
                details={"error": f"Unknown match type: {match_type}"},
            )

    def _verify_exact_match(self, expected: Any, actual: str) -> SemanticMatchResult:
        """精确匹配验证"""
        expected_str = str(expected).strip()
        actual_str = actual.strip()

        is_match = expected_str == actual_str

        return SemanticMatchResult(
            match_type=SemanticMatchType.EXACT,
            confidence=1.0 if is_match else 0.0,
            matched_elements=[expected_str] if is_match else [],
            missing_elements=[expected_str] if not is_match else [],
            extra_elements=[actual_str] if not is_match and actual_str else [],
            details={
                "expected": expected_str,
                "actual": actual_str,
                "is_exact_match": is_match,
            },
        )

    def _verify_contains_match(self, expected: Any, actual: str) -> SemanticMatchResult:
        """包含匹配验证"""
        actual_lower = actual.lower()

        if isinstance(expected, str):
            expected_items = [expected.lower()]
        elif isinstance(expected, list):
            expected_items = [item.lower() for item in expected]
        else:
            expected_items = [str(expected).lower()]

        matched = []
        missing = []

        for item in expected_items:
            if item in actual_lower:
                matched.append(item)
            else:
                missing.append(item)

        confidence = len(matched) / len(expected_items) if expected_items else 1.0

        return SemanticMatchResult(
            match_type=SemanticMatchType.CONTAINS,
            confidence=confidence,
            matched_elements=matched,
            missing_elements=missing,
            extra_elements=[],
            details={
                "expected_items": expected_items,
                "matched_count": len(matched),
                "total_count": len(expected_items),
            },
        )

    def _verify_semantic_similarity(
        self, expected: Any, actual: str
    ) -> SemanticMatchResult:
        """语义相似度验证"""
        if isinstance(expected, str):
            expected_keywords = self.keyword_extractor.extract_keywords(expected)
        elif isinstance(expected, list):
            expected_text = " ".join(expected)
            expected_keywords = self.keyword_extractor.extract_keywords(expected_text)
        else:
            expected_keywords = self.keyword_extractor.extract_keywords(str(expected))

        actual_keywords = self.keyword_extractor.extract_keywords(actual)

        if not expected_keywords:
            confidence = 1.0
            matched = []
            missing = []
        else:
            matched_keywords = expected_keywords & actual_keywords
            missing_keywords = expected_keywords - actual_keywords

            confidence = len(matched_keywords) / len(expected_keywords)
            matched = list(matched_keywords)
            missing = list(missing_keywords)

        expected_entities = self.keyword_extractor.extract_named_entities(str(expected))
        actual_entities = self.keyword_extractor.extract_named_entities(actual)

        entity_bonus = 0.0
        matched_entities = []

        for entity_type, expected_list in expected_entities.items():
            actual_list = actual_entities.get(entity_type, [])
            entity_matches = set(expected_list) & set(actual_list)

            if entity_matches:
                entity_bonus += 0.1 * (len(entity_matches) / len(expected_list))
                matched_entities.extend(list(entity_matches))

        final_confidence = min(1.0, confidence + entity_bonus)

        return SemanticMatchResult(
            match_type=SemanticMatchType.SEMANTIC_SIMILAR,
            confidence=final_confidence,
            matched_elements=matched + matched_entities,
            missing_elements=missing,
            extra_elements=list(actual_keywords - expected_keywords),
            details={
                "keyword_confidence": confidence,
                "entity_bonus": entity_bonus,
                "expected_keywords": list(expected_keywords),
                "actual_keywords": list(actual_keywords),
                "matched_entities": matched_entities,
            },
        )

    def _verify_structural_match(
        self, expected: Any, actual: str
    ) -> SemanticMatchResult:
        """结构匹配验证"""
        try:
            actual_data = json.loads(actual)

            if isinstance(expected, dict):
                expected_keys = set(expected.keys())
                actual_keys = (
                    set(actual_data.keys()) if isinstance(actual_data, dict) else set()
                )

                matched_keys = expected_keys & actual_keys
                missing_keys = expected_keys - actual_keys
                extra_keys = actual_keys - expected_keys

                confidence = (
                    len(matched_keys) / len(expected_keys) if expected_keys else 1.0
                )

                return SemanticMatchResult(
                    match_type=SemanticMatchType.STRUCTURAL,
                    confidence=confidence,
                    matched_elements=list(matched_keys),
                    missing_elements=list(missing_keys),
                    extra_elements=list(extra_keys),
                    details={
                        "expected_keys": list(expected_keys),
                        "actual_keys": list(actual_keys),
                        "is_valid_json": True,
                    },
                )
            else:
                return self._verify_keyword_match(expected, actual)

        except json.JSONDecodeError:
            return self._verify_keyword_match(expected, actual)

    def _verify_keyword_match(self, expected: Any, actual: str) -> SemanticMatchResult:
        """关键词匹配验证"""
        return self._verify_semantic_similarity(expected, actual)

    def _verify_pattern_match(self, expected: Any, actual: str) -> SemanticMatchResult:
        """模式匹配验证"""
        if isinstance(expected, str):
            try:
                pattern = re.escape(expected)
                pattern = pattern.replace(r"\*", ".*").replace(r"\?", ".")

                if re.search(pattern, actual, re.IGNORECASE):
                    return SemanticMatchResult(
                        match_type=SemanticMatchType.PATTERN_BASED,
                        confidence=1.0,
                        matched_elements=[expected],
                        missing_elements=[],
                        extra_elements=[],
                        details={"pattern": pattern, "matched": True},
                    )
                else:
                    return SemanticMatchResult(
                        match_type=SemanticMatchType.PATTERN_BASED,
                        confidence=0.0,
                        matched_elements=[],
                        missing_elements=[expected],
                        extra_elements=[],
                        details={"pattern": pattern, "matched": False},
                    )
            except re.error:
                return self._verify_contains_match(expected, actual)
        else:
            return self._verify_contains_match(expected, actual)

    def verify_tool_call_sequence(
        self, expected_tools: List[str], actual_tools: List[str]
    ) -> SemanticMatchResult:
        """验证工具调用序列"""
        if not expected_tools:
            return SemanticMatchResult(
                match_type=SemanticMatchType.STRUCTURAL,
                confidence=1.0,
                matched_elements=actual_tools,
                missing_elements=[],
                extra_elements=[],
                details={"message": "No expected tools specified"},
            )

        expected_set = set(expected_tools)
        actual_set = set(actual_tools)

        matched_tools = expected_set & actual_set
        missing_tools = expected_set - actual_set
        extra_tools = actual_set - expected_set

        sequence_score = 0.0
        if len(expected_tools) > 0 and len(actual_tools) > 0:
            expected_index = 0
            for tool in actual_tools:
                if (
                    expected_index < len(expected_tools)
                    and tool == expected_tools[expected_index]
                ):
                    expected_index += 1

            sequence_score = expected_index / len(expected_tools)

        set_confidence = len(matched_tools) / len(expected_tools)
        final_confidence = set_confidence * 0.7 + sequence_score * 0.3

        return SemanticMatchResult(
            match_type=SemanticMatchType.STRUCTURAL,
            confidence=final_confidence,
            matched_elements=list(matched_tools),
            missing_elements=list(missing_tools),
            extra_elements=list(extra_tools),
            details={
                "expected_sequence": expected_tools,
                "actual_sequence": actual_tools,
                "set_confidence": set_confidence,
                "sequence_score": sequence_score,
            },
        )


def create_semantic_verifier() -> SemanticVerifier:
    """创建语义验证器的便捷函数"""
    return SemanticVerifier()
