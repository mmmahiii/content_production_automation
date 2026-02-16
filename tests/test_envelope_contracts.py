from __future__ import annotations

import pytest

from instagram_ai_system.contracts_envelope import extract_payload, wrap_payload


def test_contracts_envelope_wrap_payload_valid() -> None:
    wrapped = wrap_payload({"foo": "bar"}, trace_id="trace-123")

    assert wrapped["schema_version"] == "1.0"
    assert wrapped["trace_id"] == "trace-123"
    assert wrapped["payload"] == {"foo": "bar"}
    assert "T" in wrapped["created_at"]


def test_contracts_envelope_extract_payload_invalid_shape_has_clear_message() -> None:
    with pytest.raises(ValueError, match="key 'payload'"):
        extract_payload({"schema_version": "1.0", "trace_id": "trace-1", "created_at": "2026-01-01T00:00:00Z"})


def test_contracts_envelope_extract_payload_legacy_payload_is_rejected_with_clear_message() -> None:
    with pytest.raises(ValueError, match="key 'payload'"):
        extract_payload({"legacy": True, "value": 3})
