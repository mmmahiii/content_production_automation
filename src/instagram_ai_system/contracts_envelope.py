from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

_SCHEMA_VERSION = "1.0"


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def wrap_payload(payload: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
    return {
        "schema_version": _SCHEMA_VERSION,
        "trace_id": trace_id or str(uuid4()),
        "created_at": _iso_utc_now(),
        "payload": payload,
    }


def extract_payload(enveloped_payload: dict[str, Any]) -> dict[str, Any]:
    payload = enveloped_payload.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("Expected envelope payload to contain object at key 'payload'.")
    return payload
