"""Pendo Server-Side Track Event integration for CogPace.

Sends track events to the Pendo Data API for analytics on session activity,
attention states, achievements, and adaptive engine decisions.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any, Optional

_PENDO_DATA_HOST = "https://data.pendo.io"
_PENDO_INTEGRATION_KEY = "22057b88-5947-43fd-aac1-00b7cb16b3d4"


def send_track_event(
    event: str,
    *,
    visitor_id: str = "anonymous",
    account_id: str = "cogpace",
    properties: Optional[dict[str, Any]] = None,
) -> bool:
    """Send a track event to the Pendo Data API. Returns True if sent."""
    payload = {
        "type": "track",
        "event": event,
        "visitorId": visitor_id,
        "accountId": account_id,
        "timestamp": int(time.time() * 1000),
    }
    if properties:
        payload["properties"] = properties

    url = f"{_PENDO_DATA_HOST}/data/track"
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-pendo-integration-key": _PENDO_INTEGRATION_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError, OSError):
        return False
