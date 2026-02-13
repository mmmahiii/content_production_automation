from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

_SCHEMA_VERSION = "1.0"
_ENVELOPE_KEYS = {"schema_version", "trace_id", "created_at", "payload"}
_LEGACY_PAYLOAD_ENV_VAR = "INSTAGRAM_AI_ACCEPT_LEGACY_PAYLOADS"


def _iso_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _legacy_acceptance_enabled() -> bool:
    return os.getenv(_LEGACY_PAYLOAD_ENV_VAR, "1").strip().lower() not in {"0", "false", "no", "off"}


def is_enveloped(payload: dict[str, Any]) -> bool:
    return isinstance(payload, dict) and _ENVELOPE_KEYS.issubset(payload.keys())


def wrap_payload(payload: dict[str, Any], trace_id: str | None = None) -> dict[str, Any]:
    return coerce_to_envelope(payload, trace_id=trace_id)


def coerce_to_envelope(
    payload: dict[str, Any],
    *,
    schema_version: str = _SCHEMA_VERSION,
    trace_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    if is_enveloped(payload):
        return payload
    if not isinstance(payload, dict):
        raise ValueError("Expected payload to be an object.")
    return {
        "schema_version": schema_version,
        "trace_id": trace_id or str(uuid4()),
        "created_at": created_at or _iso_utc_now(),
        "payload": payload,
    }


def extract_payload(
    payload_or_envelope: dict[str, Any],
    *,
    allow_legacy_payloads: bool | None = None,
) -> dict[str, Any]:
    if not isinstance(payload_or_envelope, dict):
        raise ValueError("Expected object payload.")

    payload = payload_or_envelope.get("payload")
    if is_enveloped(payload_or_envelope) or isinstance(payload, dict):
        if not isinstance(payload, dict):
            raise ValueError("Expected envelope payload to contain object at key 'payload'.")
        return payload

    legacy_enabled = _legacy_acceptance_enabled() if allow_legacy_payloads is None else allow_legacy_payloads
    if legacy_enabled:
        return payload_or_envelope

    raise ValueError(
        "Received legacy plain payload while legacy acceptance is disabled. "
        "Provide envelope with schema_version/trace_id/created_at/payload."
    )
