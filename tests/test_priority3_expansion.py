from __future__ import annotations

from datetime import datetime, timezone

from instagram_ai_system.adaptive_cycle import AdaptiveCycleCoordinator, AdaptiveLoopFlags
from instagram_ai_system.config import OptimizationConfig
from instagram_ai_system.experiment_lifecycle_management import ExperimentLifecycleManager
from instagram_ai_system.experiment_optimizer import ExperimentOptimizer
from instagram_ai_system.learning_strategy_updates import LearningLoopUpdater, ObjectiveAwareStrategyUpdater
from instagram_ai_system.mode_controller import ModeController
from instagram_ai_system.monetization_analytics import MonetizationAnalyst
from instagram_ai_system.schema_validation import SchemaValidationError, validate_payload
from instagram_ai_system.shadow_testing import ShadowTestEvaluator
from integrations.trends import InstagramHashtagScraperAdapter, RedditTrendsAdapter, TrendAggregator


class FakeInstagramClient:
    def fetch_trending_hashtags(self):
        return [
            {
                "hashtag": "#creatorai",
                "post_count": 320000,
                "growth_24h": 0.42,
                "engagement_rate": 0.07,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "url": "https://instagram.com/explore/tags/creatorai/",
            }
        ]


class FakeRedditClient:
    def fetch_hot_topics(self):
        return [
            {
                "title": "AI content pipelines",
                "hotness": 0.7,
                "velocity": 0.4,
                "created_utc": 1735689600,
                "subreddit": "marketing",
                "url": "https://reddit.com/r/marketing/test",
            }
        ]


def test_trend_aggregator_supports_instagram_and_reddit_sources() -> None:
    agg = TrendAggregator([InstagramHashtagScraperAdapter(FakeInstagramClient()), RedditTrendsAdapter(FakeRedditClient())])
    trends = agg.fetch_and_normalize()
    assert len(trends) == 2
    assert {t.source for t in trends} == {"instagram_scraper", "reddit_trends"}


def test_schema_validation_rejects_invalid_uri() -> None:
    payload = {
        "id": "post-1",
        "contentCandidateId": "cand-1",
        "platform": "instagram",
        "publishedAt": "2026-01-01T00:00:00Z",
        "url": "not-a-uri",
    }
    try:
        validate_payload(payload, "schemas/published_post.schema.json")
        assert False, "expected schema error"
    except SchemaValidationError as exc:
        assert "invalid uri format" in str(exc)


def test_adaptive_cycle_emits_mode_shadow_and_monetization_updates() -> None:
    optimization = OptimizationConfig()
    records = []
    coordinator = AdaptiveCycleCoordinator(
        optimization=optimization,
        experiment_lifecycle=ExperimentLifecycleManager(optimizer=ExperimentOptimizer(optimization)),
        learning_loop=LearningLoopUpdater(),
        objective_strategy=ObjectiveAwareStrategyUpdater(),
        mode_controller=ModeController(),
        shadow_testing=ShadowTestEvaluator(),
        monetization_analyst=MonetizationAnalyst(),
        decision_sink=records.append,
        flags=AdaptiveLoopFlags(
            enable_mode_controller=True,
            enable_shadow_testing=True,
            enable_monetization_analytics=True,
        ),
    )

    updates = coordinator.process_after_analytics(
        {
            "current_mode": "exploit",
            "explore_coef": 0.2,
            "mode_inputs": {
                "hit_rate_7d": 0.52,
                "novelty_fatigue": 0.8,
                "account_volatility": 0.3,
                "confidence_trend": 0.1,
                "monetization_drift": 0.2,
                "plateau_cycles": 0,
                "hours_since_mode_change": 7,
                "drawdown_24h": 0.05,
                "risk_budget": 0.7,
            },
            "shadow_test_results": [
                {"variant_id": "a", "views": 300, "saves": 12, "shares": 8, "comments": 3, "confidence": 0.82},
                {"variant_id": "b", "views": 260, "saves": 8, "shares": 4, "comments": 4, "confidence": 0.75},
            ],
            "monetization_metrics": {"views": 1000, "shares": 20, "saves": 30, "intent_comments": 45, "profile_actions": 18},
        },
        trace_id="trace-1",
    )

    assert "mode_controller" in updates
    assert "shadow_testing" in updates
    assert "monetization_analytics" in updates
    assert records
