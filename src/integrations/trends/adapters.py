from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, List, Protocol, Sequence


@dataclass(slots=True)
class NormalizedTrend:
    topic: str
    source: str
    score: float
    momentum: float
    observed_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class TrendSourceAdapter(Protocol):
    source_name: str

    def fetch(self) -> Iterable[dict[str, Any]]:
        """Return source-native trend records."""

    def normalize(self, payload: dict[str, Any]) -> NormalizedTrend:
        """Map source-native records into the canonical trend model."""


class GoogleTrendsAdapter:
    source_name = "google_trends"

    def __init__(self, client: Any) -> None:
        self.client = client

    def fetch(self) -> Iterable[dict[str, Any]]:
        return self.client.fetch_daily_trends()

    def normalize(self, payload: dict[str, Any]) -> NormalizedTrend:
        return NormalizedTrend(
            topic=str(payload["query"]).strip(),
            source=self.source_name,
            score=float(payload.get("interest", 0.0)) / 100.0,
            momentum=float(payload.get("delta", 0.0)),
            observed_at=_parse_ts(payload.get("timestamp")),
            metadata={"geo": payload.get("geo"), "category": payload.get("category")},
        )


class RedditTrendsAdapter:
    source_name = "reddit_trends"

    def __init__(self, client: Any) -> None:
        self.client = client

    def fetch(self) -> Iterable[dict[str, Any]]:
        return self.client.fetch_hot_topics()

    def normalize(self, payload: dict[str, Any]) -> NormalizedTrend:
        return NormalizedTrend(
            topic=str(payload["title"]).strip(),
            source=self.source_name,
            score=float(payload.get("hotness", 0.0)),
            momentum=float(payload.get("velocity", 0.0)),
            observed_at=_parse_ts(payload.get("created_utc")),
            metadata={"subreddit": payload.get("subreddit"), "url": payload.get("url")},
        )


class InstagramHashtagScraperAdapter:
    """Adapter for hashtag/reels trend signals via scraper-compatible clients."""

    source_name = "instagram_scraper"

    def __init__(self, client: Any) -> None:
        self.client = client

    def fetch(self) -> Iterable[dict[str, Any]]:
        return self.client.fetch_trending_hashtags()

    def normalize(self, payload: dict[str, Any]) -> NormalizedTrend:
        hashtag = str(payload.get("hashtag") or payload.get("tag") or "").strip()
        post_count = float(payload.get("post_count", 0.0) or 0.0)
        growth = float(payload.get("growth_24h", payload.get("growth", 0.0)) or 0.0)
        engagement = float(payload.get("engagement_rate", 0.0) or 0.0)
        score = min(1.0, (post_count / 500_000.0) + (growth * 0.6) + (engagement * 0.4))
        return NormalizedTrend(
            topic=hashtag,
            source=self.source_name,
            score=score,
            momentum=growth,
            observed_at=_parse_ts(payload.get("observed_at") or payload.get("scraped_at")),
            metadata={
                "post_count": int(post_count),
                "engagement_rate": engagement,
                "url": payload.get("url"),
            },
        )


class TrendAggregator:
    """Fetches from multiple sources and emits a normalized list sorted by score."""

    def __init__(self, adapters: Sequence[TrendSourceAdapter]) -> None:
        if len(adapters) < 2:
            raise ValueError("At least two trend sources are required.")
        self.adapters = adapters

    def fetch_and_normalize(self) -> List[NormalizedTrend]:
        trends: list[NormalizedTrend] = []
        for adapter in self.adapters:
            for row in adapter.fetch():
                trends.append(adapter.normalize(row))
        return sorted(trends, key=lambda item: item.score, reverse=True)


def _parse_ts(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str) and value:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(timezone.utc)
    return datetime.now(tz=timezone.utc)
