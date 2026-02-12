from datetime import datetime, timezone

from integrations.instagram import InstagramMetricsCollector, InstagramPublisher, PublishRequest, TransientPublishError
from integrations.trends import GoogleTrendsAdapter, RedditTrendsAdapter, TrendAggregator


class FakeGoogleClient:
    def fetch_daily_trends(self):
        return [
            {"query": "AI Reels", "interest": 92, "delta": 12.0, "timestamp": "2026-01-01T00:00:00Z", "geo": "US"}
        ]


class FakeRedditClient:
    def fetch_hot_topics(self):
        return [
            {
                "title": "Automating Instagram workflows",
                "hotness": 0.8,
                "velocity": 0.2,
                "created_utc": 1735689600,
                "subreddit": "marketing",
            }
        ]


def test_trend_aggregator_fetches_and_normalizes_multiple_sources() -> None:
    aggregator = TrendAggregator(
        adapters=[GoogleTrendsAdapter(FakeGoogleClient()), RedditTrendsAdapter(FakeRedditClient())]
    )

    trends = aggregator.fetch_and_normalize()

    assert len(trends) == 2
    assert {trend.source for trend in trends} == {"google_trends", "reddit_trends"}
    assert trends[0].score >= trends[1].score


class FakePublisherClient:
    def __init__(self):
        self.calls = 0

    def publish_post(self, payload, idempotency_key):
        self.calls += 1
        if self.calls == 1:
            raise TransientPublishError("temporary outage")
        return {"post_id": "ig_123"}


def test_publisher_uses_retry_backoff_idempotency_and_dry_run() -> None:
    sleep_calls = []
    live_client = FakePublisherClient()
    publisher = InstagramPublisher(
        client=live_client,
        dry_run=False,
        max_retries=3,
        base_backoff_seconds=0.01,
        sleeper=sleep_calls.append,
    )

    request = PublishRequest(brief_id="brief-1", media_url="https://cdn/reel.mp4", caption="Caption")
    result = publisher.publish(request)

    assert result.success is True
    assert result.platform_post_id == "ig_123"
    assert result.attempts == 2
    assert sleep_calls == [0.01]

    duplicate = publisher.publish(request)
    assert duplicate.status == "duplicate_ignored"

    dry_client = FakePublisherClient()
    dry_run_publisher = InstagramPublisher(client=dry_client, dry_run=True)
    dry_result = dry_run_publisher.publish(request)
    assert dry_result.status == "dry_run"
    assert dry_client.calls == 0
    assert any(entry.event == "publish_dry_run" for entry in dry_run_publisher.audit_log)


def test_metrics_collector_maps_native_fields_to_canonical_schema() -> None:
    collector = InstagramMetricsCollector()

    snapshot = collector.map_to_canonical(
        post_id="ig_123",
        native_payload={
            "plays": 1000,
            "likes": 120,
            "comments": 30,
            "shares": 15,
            "saved": 25,
            "profile_visits": 40,
            "avg_watch_time_seconds": 6.0,
            "video_length_seconds": 10.0,
            "captured_at": datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
        },
    )

    assert snapshot.metrics["views"] == 1000
    assert snapshot.metrics["retention"] == 0.6
    assert snapshot.metrics["profileVisits"] == 40
    assert snapshot.derived_rates["likeRate"] == 0.12
