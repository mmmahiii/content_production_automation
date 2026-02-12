from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import time
from typing import Any, Callable


@dataclass(slots=True)
class PublishRequest:
    brief_id: str
    media_url: str
    caption: str
    scheduled_at: datetime | None = None
    idempotency_key: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    approvals: dict[str, bool] = field(default_factory=dict)


@dataclass(slots=True)
class PublishResult:
    success: bool
    status: str
    idempotency_key: str
    platform_post_id: str | None
    attempts: int
    payload: dict[str, Any]


@dataclass(slots=True)
class AuditEntry:
    event: str
    idempotency_key: str
    timestamp: datetime
    payload: dict[str, Any]


class TransientPublishError(RuntimeError):
    pass


class GovernanceApprovalError(RuntimeError):
    """Raised when pre-publish governance approvals are missing."""


class InstagramPublisher:
    REQUIRED_APPROVALS = frozenset({"editorial", "compliance", "rights"})

    def __init__(
        self,
        client: Any,
        dry_run: bool = False,
        max_retries: int = 3,
        base_backoff_seconds: float = 0.5,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self.client = client
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.base_backoff_seconds = base_backoff_seconds
        self.sleeper = sleeper or time.sleep
        self._seen_idempotency_keys: set[str] = set()
        self.audit_log: list[AuditEntry] = []

    def publish(self, request: PublishRequest) -> PublishResult:
        self._enforce_approval_gate(request)
        key = request.idempotency_key or self._build_idempotency_key(request)
        payload = self._payload(request, key)
        self._audit("publish_attempt", key, payload)

        if key in self._seen_idempotency_keys:
            result = PublishResult(
                success=True,
                status="duplicate_ignored",
                idempotency_key=key,
                platform_post_id=None,
                attempts=0,
                payload=payload,
            )
            self._audit("publish_duplicate", key, payload)
            return result

        if self.dry_run:
            self._seen_idempotency_keys.add(key)
            self._audit("publish_dry_run", key, payload)
            return PublishResult(
                success=True,
                status="dry_run",
                idempotency_key=key,
                platform_post_id=None,
                attempts=0,
                payload=payload,
            )

        attempt = 0
        while True:
            attempt += 1
            try:
                response = self.client.publish_post(payload=payload, idempotency_key=key)
                platform_post_id = str(response["post_id"])
                self._seen_idempotency_keys.add(key)
                self._audit("publish_success", key, {**payload, "post_id": platform_post_id})
                return PublishResult(
                    success=True,
                    status="published",
                    idempotency_key=key,
                    platform_post_id=platform_post_id,
                    attempts=attempt,
                    payload=payload,
                )
            except TransientPublishError as exc:
                self._audit("publish_retry", key, {**payload, "attempt": attempt, "error": str(exc)})
                if attempt >= self.max_retries:
                    self._audit("publish_failed", key, {**payload, "attempt": attempt, "error": str(exc)})
                    return PublishResult(
                        success=False,
                        status="failed",
                        idempotency_key=key,
                        platform_post_id=None,
                        attempts=attempt,
                        payload=payload,
                    )
                self.sleeper(self.base_backoff_seconds * (2 ** (attempt - 1)))

    def _enforce_approval_gate(self, request: PublishRequest) -> None:
        missing = sorted([approval for approval in self.REQUIRED_APPROVALS if not request.approvals.get(approval, False)])
        if missing:
            payload = {
                "brief_id": request.brief_id,
                "missing_approvals": missing,
                "provided_approvals": request.approvals,
            }
            self._audit("publish_blocked_missing_approvals", request.idempotency_key or "pending", payload)
            raise GovernanceApprovalError(
                "Publish blocked by governance gate; missing required approvals: " + ", ".join(missing)
            )

    def _payload(self, request: PublishRequest, idempotency_key: str) -> dict[str, Any]:
        return {
            "brief_id": request.brief_id,
            "media_url": request.media_url,
            "caption": request.caption,
            "scheduled_at": request.scheduled_at.astimezone(timezone.utc).isoformat()
            if request.scheduled_at
            else None,
            "metadata": request.metadata,
            "idempotency_key": idempotency_key,
        }

    def _build_idempotency_key(self, request: PublishRequest) -> str:
        basis = {
            "brief_id": request.brief_id,
            "media_url": request.media_url,
            "caption": request.caption,
            "scheduled_at": request.scheduled_at.astimezone(timezone.utc).isoformat()
            if request.scheduled_at
            else None,
        }
        return hashlib.sha256(json.dumps(basis, sort_keys=True).encode("utf-8")).hexdigest()

    def _audit(self, event: str, key: str, payload: dict[str, Any]) -> None:
        self.audit_log.append(
            AuditEntry(
                event=event,
                idempotency_key=key,
                timestamp=datetime.now(tz=timezone.utc),
                payload=payload,
            )
        )
