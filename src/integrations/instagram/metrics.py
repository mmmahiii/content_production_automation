from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class CanonicalPerformanceSnapshot:
    id: str
    published_post_id: str
    captured_at: datetime
    window: str
    metrics: dict[str, float | int]
    derived_rates: dict[str, float]


class InstagramMetricsCollector:
    """Maps Instagram-native insights payloads to canonical performance schema."""

    def map_to_canonical(self, post_id: str, native_payload: dict[str, Any], window: str = "24h") -> CanonicalPerformanceSnapshot:
        views = int(native_payload.get("plays", 0))
        likes = int(native_payload.get("likes", 0))
        comments = int(native_payload.get("comments", 0))
        shares = int(native_payload.get("shares", 0))
        saves = int(native_payload.get("saved", 0))
        profile_visits = int(native_payload.get("profile_visits", 0))
        avg_watch_time = float(native_payload.get("avg_watch_time_seconds", 0.0))
        video_length = float(native_payload.get("video_length_seconds", 0.0))
        retention = min(1.0, (avg_watch_time / video_length)) if video_length > 0 else 0.0

        denom = max(views, 1)
        derived_rates = {
            "likeRate": likes / denom,
            "commentRate": comments / denom,
            "shareRate": shares / denom,
            "saveRate": saves / denom,
            "profileVisitRate": profile_visits / denom,
        }

        captured_at = _parse_ts(native_payload.get("captured_at"))
        snapshot_id = f"{post_id}:{window}:{captured_at.isoformat()}"

        return CanonicalPerformanceSnapshot(
            id=snapshot_id,
            published_post_id=post_id,
            captured_at=captured_at,
            window=window,
            metrics={
                "views": views,
                "retention": retention,
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "saves": saves,
                "profileVisits": profile_visits,
            },
            derived_rates=derived_rates,
        )


def _parse_ts(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if isinstance(value, str) and value:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    return datetime.now(tz=timezone.utc)
