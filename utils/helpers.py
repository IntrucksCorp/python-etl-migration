from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any


def safe_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def safe_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1", "yes")


def parse_date(value: Any) -> str | None:
    """Return ISO date string (YYYY-MM-DD) or None."""
    if value is None:
        return None
    raw = str(value).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            pass
    return None


def split_full_name(full_name: str | None) -> tuple[str, str]:
    """Split 'First Last' → ('First', 'Last'). Single word → ('Name', '')."""
    if not full_name:
        return ("", "")
    parts = full_name.strip().split(None, 1)
    return (parts[0], parts[1] if len(parts) > 1 else "")


def years_since(year_str: Any) -> int | None:
    """Return current year minus the given year, or None."""
    y = safe_int(year_str)
    if y is None:
        return None
    return date.today().year - y
