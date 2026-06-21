"""Competition profile loader — one codebase, per-hackathon narrative."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_PROFILES_DIR = Path(__file__).resolve().parent
_DEFAULT_ID = "stem_education"

_PROFILE_CACHE: dict[str, dict[str, Any]] = {}


def list_profile_ids() -> list[str]:
    return sorted(p.stem for p in _PROFILES_DIR.glob("*.json"))


def load_profile(profile_id: str | None = None) -> dict[str, Any]:
    pid = (profile_id or os.getenv("COGPACE_PROFILE") or _DEFAULT_ID).strip().lower()
    if pid in _PROFILE_CACHE:
        return _PROFILE_CACHE[pid]

    path = _PROFILES_DIR / f"{pid}.json"
    if not path.is_file():
        path = _PROFILES_DIR / f"{_DEFAULT_ID}.json"
        pid = _DEFAULT_ID

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    data["id"] = data.get("id", pid)
    _PROFILE_CACHE[pid] = data
    return data


def resolve_profile_from_query(query_value: str | None) -> dict[str, Any]:
    """Map URL aliases to profile ids."""
    if not query_value:
        return load_profile(None)
    alias = query_value.strip().lower().replace("-", "_")
    aliases = {
        "default": "stem_education",
        "dsh": "stem_education",
        "youth_code": "youth_code_social",
        "youth_social": "youth_code_social",
        "youth_education": "youth_code_education",
        "career": "youth_code_education",
        "gitlab": "gitlab_devops",
        "splunk": "splunk_observability",
        "mtp": "mind_the_product",
        "novus": "mind_the_product",
    }
    return load_profile(aliases.get(alias, alias))
