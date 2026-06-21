"""Local JSON event log — demo telemetry without Splunk/Pendo."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_LOG_DIR = Path(__file__).resolve().parent.parent / "session_logs"


def append_event(session_id: str, event_type: str, payload: dict[str, Any]) -> Path | None:
    if not session_id:
        return None
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = _LOG_DIR / f"{session_id}.jsonl"
    record = {
        "ts": int(time.time()),
        "type": event_type,
        **payload,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def export_session_summary(session_id: str, summary: dict[str, Any]) -> Path | None:
    if not session_id:
        return None
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = _LOG_DIR / f"{session_id}_summary.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    return path
