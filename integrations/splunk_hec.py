"""Optional Splunk HEC integration for CogPace session events.

Set SPLUNK_HEC_URL and SPLUNK_HEC_TOKEN to enable. Used for Splunk Agentic Ops
Hackathon (Observability track): attention state transitions as operational telemetry.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


def _hec_configured() -> bool:
    return bool(os.getenv("SPLUNK_HEC_URL") and os.getenv("SPLUNK_HEC_TOKEN"))


def send_attention_event(
    *,
    session_id: str,
    question_id: str,
    subject: str,
    state: str,
    f_att: float,
    r: float,
    s: float,
    correct: bool,
    response_ms: int,
    extra: dict[str, Any] | None = None,
) -> bool:
    """Send one attention-state event to Splunk HEC. Returns True if sent."""
    if not _hec_configured():
        return False

    event: dict[str, Any] = {
        "time": int(time.time()),
        "host": "cogpace",
        "source": "cogpace:mfa_attention",
        "sourcetype": "cogpace:attention:v1",
        "event": {
            "session_id": session_id,
            "question_id": question_id,
            "subject": subject,
            "attention_state": state,
            "f_att": round(f_att, 4),
            "r": round(r, 4),
            "S": round(s, 4),
            "correct": correct,
            "response_ms": response_ms,
            **(extra or {}),
        },
    }

    url = os.environ["SPLUNK_HEC_URL"].rstrip("/") + "/services/collector/event"
    token = os.environ["SPLUNK_HEC_TOKEN"]
    body = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Splunk {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False
