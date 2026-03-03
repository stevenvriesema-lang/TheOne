"""Simple persistent memory storage for small user facts.

This module stores a tiny JSON with key-value pairs and exposes a
`get_memory()` and `update_memory()` helper used to prepend context to LLM prompts.
It's intentionally minimal and safe — only stores non-sensitive short facts.
"""
import json
import os
from typing import Dict

_MEM_PATH = os.path.join(os.path.dirname(__file__), '..', 'assistant_memory.json')

def _load() -> Dict[str, str]:
    try:
        if os.path.exists(_MEM_PATH):
            with open(_MEM_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save(data: Dict[str, str]):
    try:
        with open(_MEM_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def get_memory_summary(max_items: int = 5) -> str:
    data = _load()
    if not data:
        return ''
    items = []
    for k, v in list(data.items())[:max_items]:
        items.append(f"{k}: {v}")
    return ' | '.join(items)

def update_memory(key: str, value: str):
    d = _load()
    d[key] = value
    _save(d)

def get_memory(key: str) -> str | None:
    d = _load()
    return d.get(key)

def delete_memory(key: str):
    d = _load()
    if key in d:
        d.pop(key)
        _save(d)

def clear_memory():
    _save({})
