"""
RobinHood AI - Request Validation Helpers

Small, dependency-free validators used by the routes so every endpoint returns a
clean 400 with a safe message instead of a 500 that leaks internals. None of the
helpers echo raw values or exception strings back to the client.
"""


def require_fields(data: dict | None, *fields: str) -> str | None:
    """Return an error string naming the first missing field, else None."""
    if not isinstance(data, dict):
        return "Request body must be a JSON object."
    for f in fields:
        if f not in data or data[f] in (None, ""):
            return f"Missing required field: '{f}'."
    return None


def as_nonneg_number(value, name: str) -> tuple[float | None, str | None]:
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None, f"Field '{name}' must be a number."
    if num < 0:
        return None, f"Field '{name}' cannot be negative."
    if num > 1e11:  # 100 billion ceiling guards absurd/DoS inputs
        return None, f"Field '{name}' is out of an acceptable range."
    return num, None


def as_length_limited(value, name: str, max_len: int) -> tuple[str | None, str | None]:
    if value is None:
        return None, None
    text = str(value)
    if len(text) > max_len:
        return None, f"Field '{name}' exceeds maximum length of {max_len}."
    return text, None


def clamp_int(value, lo: int, hi: int) -> int:
    try:
        n = int(value)
    except (TypeError, ValueError):
        return lo
    return max(lo, min(n, hi))
