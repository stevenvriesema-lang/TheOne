"""Lightweight in-memory dialogue history for short-term context.

Use `add_turn(role, text)` to record turns and `get_recent_summary(n)` to
produce a short plaintext summary of the last `n` turns for prompt injection.
"""
from collections import deque
from typing import Deque, Tuple

_HISTORY: Deque[Tuple[str, str]] = deque(maxlen=50)


def add_turn(role: str, text: str):
    _HISTORY.append((role, text))


def get_recent(n: int = 3) -> list:
    return list(_HISTORY)[-n:]


def get_recent_summary(n: int = 3) -> str:
    items = get_recent(n)
    if not items:
        return ''
    parts = []
    for r, t in items:
        parts.append(f"{r}: {t}")
    return ' | '.join(parts)
