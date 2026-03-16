"""Expression parser for workflow condition nodes. Supports ==, >, <, contains."""
from __future__ import annotations

import re
from typing import Any


def _get_value(context: dict[str, Any], path: str) -> Any:
    """Resolve dot-path (e.g. article_length, _last_output.content) from context."""
    parts = [p for p in path.strip().split(".") if p]
    value: Any = context
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value


def _parse_literal(s: str) -> Any:
    """Parse string literal to int, float, or string."""
    s = s.strip()
    if not s:
        return ""
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if s.lower() == "null":
        return None
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        return s[1:-1]
    return s


# Operators in order of match (longer first to avoid partial matches)
_OPERATORS = [
    ("contains", lambda left, right: (str(left) if left is not None else "").find(str(right)) >= 0 if right is not None else False),
    (">=", lambda left, right: left is not None and right is not None and left >= right),
    ("<=", lambda left, right: left is not None and right is not None and left <= right),
    ("==", lambda left, right: left == right),
    ("!=", lambda left, right: left != right),
    (">", lambda left, right: left is not None and right is not None and left > right),
    ("<", lambda left, right: left is not None and right is not None and left < right),
]


def parse_expression(expr: str) -> tuple[str, str, str]:
    """
    Parse expression like 'article_length > 1000' or 'content contains error'.
    Returns (left_path, operator, right_str). right_str may be literal or context path.
    """
    expr = (expr or "").strip()
    if not expr:
        raise ValueError("Empty expression")

    for op, _ in _OPERATORS:
        idx = expr.find(op)
        if idx >= 0:
            left = expr[:idx].strip()
            right = expr[idx + len(op) :].strip()
            if not left:
                raise ValueError(f"Missing left operand before '{op}'")
            if not right:
                raise ValueError(f"Missing right operand after '{op}'")
            return (left, op, right)
    raise ValueError(f"Unsupported or malformed expression: {expr!r}")


def _resolve_right(right_str: str, context: dict[str, Any]) -> Any:
    """Resolve right operand: literal (number, quoted, true/false/null) or context path."""
    right_str = right_str.strip()
    if (right_str.startswith('"') and right_str.endswith('"')) or (right_str.startswith("'") and right_str.endswith("'")):
        return right_str[1:-1]
    if right_str.lower() in ("true", "false", "null"):
        return _parse_literal(right_str)
    try:
        return int(right_str)
    except ValueError:
        pass
    try:
        return float(right_str)
    except ValueError:
        pass
    path_val = _get_value(context, right_str)
    if path_val is not None or "." in right_str or right_str in context:
        return path_val
    return right_str


def evaluate_expression(expr: str, context: dict[str, Any]) -> bool:
    """
    Evaluate condition expression against execution context.
    Examples:
        article_length > 1000
        status == approved
        content contains error
        count < 5
    """
    left_path, op_str, right_str = parse_expression(expr)
    left_val = _get_value(context, left_path)
    right_val = _resolve_right(right_str, context)

    for op, fn in _OPERATORS:
        if op == op_str:
            return fn(left_val, right_val)
    return False
