"""Shared utility functions."""

from datetime import datetime
from typing import List, Dict, Any


def get_timestamp() -> str:
    return datetime.now().isoformat()


def truncate_text(text: str, max_length: int = 200) -> str:
    return text if len(text) <= max_length else text[:max_length] + "..."


def get_recent_observations_summary(
    observations: List[Dict[str, Any]], max_items: int = 3
) -> str:
    if not observations:
        return "无观察记录"
    recent = observations[-max_items:]
    lines = []
    for obs in recent:
        step = obs.get("step", "?")
        action = obs.get("action", "unknown")
        result = obs.get("result", "")
        result = (
            truncate_text(result, 200) if isinstance(result, str) else str(result)[:200]
        )
        lines.append(f"步骤 {step}: {action} -> {result}")
    return "\n".join(lines)
