"""Condition expression parser and evaluator."""

import re
from typing import Any, Dict, Optional


class ConditionContext:
    """Context object for condition evaluation - wraps result with helper methods."""

    def __init__(self, result: Any):
        self._result = result

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the result dict or return default."""
        if isinstance(self._result, dict):
            return self._result.get(key, default)
        return getattr(self._result, key, default) if hasattr(self._result, key) else default

    def contains(self, substring: str) -> bool:
        """Check if result contains a substring."""
        if self._result is None:
            return False
        return substring in str(self._result)

    def __str__(self) -> str:
        return str(self._result) if self._result is not None else ""

    def __bool__(self) -> bool:
        if self._result is None:
            return False
        if isinstance(self._result, bool):
            return self._result
        if isinstance(self._result, (dict, list, str)):
            return len(self._result) > 0
        return True

    def __eq__(self, other: Any) -> bool:
        """Support direct comparison: result == value."""
        if isinstance(other, ConditionContext):
            return self._result == other._result
        return self._result == other

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __is__(self, other: Any) -> bool:
        """Support 'is None' checks."""
        if other is None:
            return self._result is None
        if other is True:
            return self._result is True
        if other is False:
            return self._result is False
        return self._result is other


def eval_condition(expression: str, context: Any) -> bool:
    """
    Evaluate a condition expression against a result.

    Supported patterns:
    - result.contains("substring")
    - result.get("key", default)
    - result.get("key") == "value"
    - result.status == "success"
    - result is None / result is not None
    - result == value / result != value
    - Comparison operators: <, >, <=, >=

    Args:
        expression: The condition expression string
        context: The result to evaluate against

    Returns:
        True if condition is met, False otherwise
    """
    if not expression:
        return True

    # Create context wrapper
    ctx = ConditionContext(context)

    # Build evaluation namespace
    eval_globals = {
        "result": ctx,
        "True": True,
        "False": False,
        "None": None,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "len": len,
    }

    try:
        # Replace result.X with ctx.X for cleaner expressions
        # Handle common patterns
        normalized = expression

        # result.contains("x") -> ctx.contains("x")
        normalized = re.sub(r"\bresult\.contains\(", "ctx.contains(", normalized)

        # result.get("x", d) -> ctx.get("x", d)
        normalized = re.sub(r"\bresult\.get\(", "ctx.get(", normalized)

        # result["x"] -> ctx._result["x"]
        normalized = re.sub(r"result\[", "ctx._result[", normalized)

        # result.attr -> ctx.get("attr") or ctx._result.attr
        def replace_attr(match):
            attr = match.group(1)
            return f'ctx.get("{attr}")'

        normalized = re.sub(r"\bresult\.(\w+)(?!\()", replace_attr, normalized)

        # Handle "result is None" / "result is not None" specially
        # Python's 'is' cannot be overloaded, so we transform it
        if re.search(r"\bresult\s+is\s+None\b", normalized):
            normalized = re.sub(r"\bresult\s+is\s+None\b", "ctx._result is None", normalized)
        if re.search(r"\bresult\s+is\s+not\s+None\b", normalized):
            normalized = re.sub(r"\bresult\s+is\s+not\s+None\b", "ctx._result is not None", normalized)
        if re.search(r"\bresult\s+is\s+True\b", normalized):
            normalized = re.sub(r"\bresult\s+is\s+True\b", "ctx._result is True", normalized)
        if re.search(r"\bresult\s+is\s+False\b", normalized):
            normalized = re.sub(r"\bresult\s+is\s+False\b", "ctx._result is False", normalized)

        result = eval(normalized, eval_globals, {"ctx": ctx})
        return bool(result)

    except Exception:
        # On any evaluation error, return False (fail safe)
        return False


def parse_condition_expression(expression: str) -> Optional[Dict[str, str]]:
    """
    Parse a condition expression into its components.

    Returns dict with 'then_node' and 'else_node' if valid, None otherwise.
    """
    # Simple parsing - for complex expressions, just return None
    if not expression or "then" not in expression.lower() or "else" not in expression.lower():
        return None

    return {"expression": expression}
