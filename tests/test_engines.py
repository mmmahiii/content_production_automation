from __future__ import annotations

from datetime import datetime

import pytest

from instagram_ai_system import CreativityMode
from instagram_ai_system.config import OptimizationConfig, PageStrategyConfig
from instagram_ai_system.creativity_engine import (
    CreativityEngine,
    CreativityGuardrails,
    TopicPolicyViolationError,
)
from instagram_ai_system.experiment_optimizer import ExperimentOptimizer
from instagram_ai_system.models import PublishedPostMetrics, ReelSignal, TrendInsight
from instagram_ai_system.orchestration import InstagramAISystem
from instagram_ai_system.trend_intelligence import TrendIntelligenceEngine


def _signal(
    reel_id: str,
    hook: str,
    duration: float,
    retention: list[float],
    shares: int,
    saves: int,
    comments: int,
) -> ReelSignal:
    return ReelSignal(
        reel_id=reel_id,
        niche="ai marketing",
        hook_style=hook,
        duration_seconds=duration,
        caption_length=120,
        audio_trend_score=0.5,
        visual_novelty_score=0.4,
        retention_curve=retention,
        shares=shares,
        saves=saves,
        comments=comments,
        posted_at=datetime.utcnow(),
    )


def test_trend_intelligence_extracts_sorted_patterns_and_honors_limit() -> None:
    engine = TrendIntelligenceEngine()
    signals = [
        _signal("a", "curiosity_gap", 9.9, [0.9, 0.8], 20, 18, 5),
        _signal("b", "curiosity_gap", 10.0, [0.85, 0.8], 18, 16, 5),
        _signal("c", "direct_teach", 34.9, [], 8, 8, 3),
        _signal("d", "direct_teach", 35.0, [0.2], 3, 3, 1),
    ]

    insights = engine.extract_top_patterns(signals, limit=3)

    assert len(insights) == 3
    assert [ins.score for ins in insights] == sorted([ins.score for ins in insights], reverse=True)
    patterns = {ins.pattern for ins in insights}
    assert any(p.startswith("hook:") for p in patterns)
    assert any(p.startswith("duration:") for p in patterns)


def test_trend_duration_bucket_boundaries() -> None:
    assert TrendIntelligenceEngine._duration_bucket(0) == "0-9s"
    assert TrendIntelligenceEngine._duration_bucket(9.99) == "0-9s"
    assert TrendIntelligenceEngine._duration_bucket(10) == "10-19s"
    assert TrendIntelligenceEngine._duration_bucket(19.99) == "10-19s"
    assert TrendIntelligenceEngine._duration_bucket(20) == "20-34s"
    assert TrendIntelligenceEngine._duration_bucket(34.99) == "20-34s"
    assert TrendIntelligenceEngine._duration_bucket(35) == "35s+"


def test_creativity_engine_respects_modes_and_guardrails() -> None:
    guardrails = CreativityGuardrails(
        banned_topics=["forbidden phrase"],
        mandatory_disclosures=["Disclosure required."],
    )
    engine = CreativityEngine(guardrails=guardrails)
    trends = [TrendInsight(pattern="hook:curiosity_gap", score=10.0, rationale="r")]

    safe = engine.generate_brief("B2B Sales", "operators", CreativityMode.SAFE, trends)
    full = engine.generate_brief("B2B Sales", "operators", CreativityMode.FULL, trends)

    assert "practical" in safe.topic
    assert "Disclosure required." in safe.caption
    assert "high-risk, high-reward" in full.caption
    assert any("Surprising twist" in scene for scene in full.storyboard)
    assert "#b2bsales" in safe.hashtags


def test_creativity_engine_caption_handles_empty_mandatory_disclosures() -> None:
    guardrails = CreativityGuardrails(
        banned_topics=["x"],
        mandatory_disclosures=[],
    )
    engine = CreativityEngine(guardrails=guardrails)

    caption = engine._caption("topic", "operators", CreativityMode.SAFE)

    assert caption.endswith("This content is AI-assisted.")
    assert "today. This content" in caption


def test_creativity_engine_caption_avoids_trailing_space_when_disclosure_empty() -> None:
    guardrails = CreativityGuardrails(
        banned_topics=["x"],
        mandatory_disclosures=[""],
    )
    engine = CreativityEngine(guardrails=guardrails)

    caption = engine._caption("topic", "operators", CreativityMode.SAFE)

    assert caption.endswith("today.")
    assert not caption.endswith(" ")


def test_experiment_optimizer_exploitation_and_exploration(monkeypatch: pytest.MonkeyPatch) -> None:
    optimizer = ExperimentOptimizer(OptimizationConfig(epsilon_exploration=0.0))

    # Unseen candidates are selected first in order.
    assert optimizer.choose_archetype(["a", "b"]) == "a"

    metrics_low = PublishedPostMetrics("id-1", views=10, likes=10, comments=0, shares=0, saves=0, avg_watch_time_seconds=1)
    metrics_high = PublishedPostMetrics("id-2", views=100, likes=20, comments=10, shares=10, saves=10, avg_watch_time_seconds=5)
    optimizer.register_result("a", metrics_low)
    optimizer.register_result("b", metrics_high)

    # With no exploration, highest avg reward wins.
    assert optimizer.choose_archetype(["a", "b"]) == "b"

    # Force exploration branch.
    monkeypatch.setattr("instagram_ai_system.experiment_optimizer.random", lambda: 0.01)
    optimizer.config.epsilon_exploration = 1.0
    assert optimizer.choose_archetype(["a", "b"]) == "a"


def test_orchestration_handles_empty_personas_and_unknown_metrics_brief() -> None:
    strategy = PageStrategyConfig(
        niche="AI Marketing",
        target_personas=[],
        posting_times_utc=["12:00"],
        max_posts_per_day=2,
        creativity_mode=CreativityMode.BALANCED,
    )
    system = InstagramAISystem(strategy=strategy)

    cycle = system.run_creation_cycle([])
    assert cycle.selected_briefs == []
    assert cycle.top_patterns == []

    reward = system.register_post_metrics(
        PublishedPostMetrics(
            brief_id="missing",
            views=100,
            likes=25,
            comments=6,
            shares=8,
            saves=5,
            avg_watch_time_seconds=3.5,
        )
    )
    assert reward > 0
    assert system.optimizer.arms["problem_solution"].pulls == 1
