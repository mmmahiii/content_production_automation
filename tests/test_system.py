from datetime import datetime, timedelta

from instagram_ai_system import CreativityMode, InstagramAISystem, PageStrategyConfig, ReelSignal


def make_signal(i: int) -> ReelSignal:
    return ReelSignal(
        reel_id=f"r{i}",
        niche="ai marketing",
        hook_style="curiosity_gap" if i % 2 else "shock_statement",
        duration_seconds=8 + i,
        caption_length=120,
        audio_trend_score=0.6,
        visual_novelty_score=0.7,
        retention_curve=[0.95, 0.8, 0.7],
        shares=25 + i,
        saves=30 + i,
        comments=10 + i,
        posted_at=datetime.utcnow() - timedelta(days=i),
    )


def test_creation_cycle_limits_posts_and_sets_creativity_mode() -> None:
    strategy = PageStrategyConfig(
        niche="AI Marketing",
        target_personas=["freelancers", "agency founders"],
        posting_times_utc=["12:00", "18:00"],
        max_posts_per_day=3,
        creativity_mode=CreativityMode.FULL,
    )
    system = InstagramAISystem(strategy=strategy)
    cycle = system.run_creation_cycle(make_signal(i) for i in range(15))

    assert len(cycle.selected_briefs) == 3
    assert cycle.top_patterns
    assert all(brief.creativity_mode == CreativityMode.FULL for brief in cycle.selected_briefs)
