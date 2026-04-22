"""Shared utilities"""

import json
import re
from typing import Any, Dict, List


_TOOL_XML_PATTERN = re.compile(r'<tool\s+name="([^"]+)"\s+args=\'([^\']*)\'/>')


def extract_xml_tool_calls(text: str) -> List[Dict[str, Any]]:
    """Parse <tool name="..." args='...'> XML tags from text into structured dicts."""
    result = []
    for match in _TOOL_XML_PATTERN.finditer(text):
        try:
            name = match.group(1)
            args = json.loads(match.group(2))
            result.append({"name": name, "arguments": args})
        except (json.JSONDecodeError, ValueError):
            pass
    return result


def normalize_tool_calls(raw_calls: List) -> List[Dict[str, Any]]:
    """Normalize mixed tool call formats to {"name": ..., "arguments": ...} dicts.

    Accepts:
        - dicts with "name"/"arguments" keys (structured format)
        - tuples of (name, args) (legacy format)
    Returns a list of normalized dicts.
    """
    result = []
    for tc in raw_calls:
        if isinstance(tc, dict):
            result.append(tc)
        elif isinstance(tc, tuple):
            name, args = tc
            result.append({"name": name, "arguments": args})
    return result


def extract_json(text: str) -> dict:
    """Extract JSON object from text, handling markdown code blocks and plain JSON.

    Finds the first {...} block or JSON inside ```json ``` fences.
    """

    # Try all fenced code blocks, return first one that parses as JSON
    for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE):
        candidate = match.group(1).strip()
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue

    # Fall back to brace-based extraction
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start : end + 1])

    return json.loads(text)
