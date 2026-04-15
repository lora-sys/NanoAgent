"""标记系统 - 简洁的AI行为标记解析器

使用内置函数实现，零依赖，符合nano风格。
"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


# 标记类型定义
MARKER_TYPES = {
    "THINKING": "AI内部推理过程",
    "PLAN": "任务分解和执行计划",
    "TOOL": "工具调用",
    "OBSERVATION": "工具执行结果",
    "REFLECTION": "自我反思和调整",
    "RESPONSE": "最终响应内容",
}


@dataclass
class MarkedSection:
    """标记化的内容块"""
    marker_type: str
    content: str
    metadata: Dict[str, str]
    raw: str


class MarkerParser:
    """标记解析器 - 使用正则表达式解析标记"""

    # 匹配 <|TYPE|>content<|/TYPE|> 或 <|TYPE|attr="value"|>content<|/TYPE|>
    _PATTERN = re.compile(
        r'<\|(\w+)\|(?:([^>]+)\|)?>(.*?)<\|/\1\|>',
        re.DOTALL
    )

    def __init__(self):
        self._sections: List[MarkedSection] = []

    def parse(self, text: str) -> List[MarkedSection]:
        """解析标记化文本"""
        self._sections = []
        for match in self._PATTERN.finditer(text):
            marker_type = match.group(1)
            attrs_str = match.group(2)  # 可能为None
            content = match.group(3).strip()
            raw = match.group(0)

            # 解析属性
            metadata = {}
            if attrs_str and attrs_str.strip():
                metadata = self._parse_attributes(attrs_str)

            section = MarkedSection(
                marker_type=marker_type,
                content=content,
                metadata=metadata,
                raw=raw
            )
            self._sections.append(section)

        return self._sections

    def _parse_attributes(self, attrs_str: str) -> Dict[str, str]:
        """解析属性字符串，支持单引号和双引号"""
        metadata = {}
        i = 0
        n = len(attrs_str)

        while i < n:
            # 跳过空白
            while i < n and attrs_str[i].isspace():
                i += 1
            if i >= n:
                break

            # 读取key
            key_start = i
            while i < n and attrs_str[i] != '=' and not attrs_str[i].isspace():
                i += 1
            key = attrs_str[key_start:i].strip()

            if not key:
                break

            # 跳过=和空白
            while i < n and (attrs_str[i] == '=' or attrs_str[i].isspace()):
                i += 1

            # 读取value（带引号）
            if i < n and attrs_str[i] in ('"', "'"):
                quote = attrs_str[i]
                i += 1
                value_start = i
                # 找到匹配的结束引号
                while i < n:
                    if attrs_str[i] == quote:
                        # 检查是否转义
                        if i == 0 or attrs_str[i-1] != '\\':
                            break
                    i += 1
                value = attrs_str[value_start:i]
                i += 1  # 跳过结束引号
                metadata[key] = value
            else:
                # 无引号的值，读到空白或结尾
                value_start = i
                while i < n and not attrs_str[i].isspace():
                    i += 1
                value = attrs_str[value_start:i]
                metadata[key] = value

        return metadata

    def extract_by_type(self, marker_type: str) -> List[MarkedSection]:
        """提取特定类型的所有标记块"""
        return [s for s in self._sections if s.marker_type == marker_type]

    def extract_first(self, marker_type: str) -> Optional[MarkedSection]:
        """提取特定类型的第一个标记块"""
        for s in self._sections:
            if s.marker_type == marker_type:
                return s
        return None

    def remove_markers(self, text: str) -> str:
        """移除所有标记，返回纯文本"""
        return self._PATTERN.sub(r'\3', text)


class MarkerBuilder:
    """标记构建器 - 生成标记化文本"""

    @staticmethod
    def build(marker_type: str, content: str, **metadata) -> str:
        """构建标记化内容

        Args:
            marker_type: 标记类型 (THINKING, PLAN, TOOL, etc.)
            content: 内容
            **metadata: 元数据 (如 name="read_file", args="...")

        Returns:
            标记化字符串
        """
        # 构建属性字符串
        attrs = []
        for key, value in metadata.items():
            attrs.append(f'{key}="{value}"')
        attr_str = ' '.join(attrs) if attrs else ''

        # 构建标记
        if attr_str:
            return f'<|{marker_type}|{attr_str}|>\n{content}\n<|/{marker_type}|>'
        else:
            return f'<|{marker_type}|>\n{content}\n<|/{marker_type}|>'

    @staticmethod
    def thinking(content: str) -> str:
        """构建思考标记"""
        return MarkerBuilder.build("THINKING", content)

    @staticmethod
    def plan(content: str) -> str:
        """构建计划标记"""
        return MarkerBuilder.build("PLAN", content)

    @staticmethod
    def tool(name: str, args: Dict, description: str = "") -> str:
        """构建工具调用标记"""
        import json
        args_str = json.dumps(args, ensure_ascii=False)
        return MarkerBuilder.build("TOOL", description, name=name, args=args_str)

    @staticmethod
    def observation(content: str) -> str:
        """构建观察标记"""
        return MarkerBuilder.build("OBSERVATION", content)

    @staticmethod
    def reflection(content: str) -> str:
        """构建反思标记"""
        return MarkerBuilder.build("REFLECTION", content)

    @staticmethod
    def response(content: str) -> str:
        """构建响应标记"""
        return MarkerBuilder.build("RESPONSE", content)


# 便捷函数
def parse_markers(text: str) -> List[MarkedSection]:
    """解析标记化文本（便捷函数）"""
    return MarkerParser().parse(text)


def build_marker(marker_type: str, content: str, **metadata) -> str:
    """构建标记（便捷函数）"""
    return MarkerBuilder.build(marker_type, content, **metadata)
