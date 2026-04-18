"""Shared utilities"""

import json
import re


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
