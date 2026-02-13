from __future__ import annotations

from instagram_ai_system.niche_strategy_engine import NicheStrategyEngine
from instagram_ai_system.models import ExperimentOutcome


def test_niche_strategy_engine_ranks_and_builds_report() -> None:
    engine = NicheStrategyEngine()
    candidates = engine.generate_candidates(seed_categories=["AI marketing", "B2B automation"], variants_per_seed=2)
    signals = engine.collect_signals(candidates)

    ranked = engine.score_candidates(candidates, signals)
    portfolio = engine.select_portfolio(ranked, top_k=3)
    report = engine.build_decision_report(ranked, portfolio)

    assert len(candidates) == 4
    assert ranked
    assert ranked[0].success_score >= ranked[-1].success_score
    assert len(portfolio) == 3
    assert report.portfolio_plan[0].planned_posts == 12


def test_niche_strategy_engine_evaluates_results() -> None:
    engine = NicheStrategyEngine()
    result = engine.evaluate_results(
        [
            ExperimentOutcome("n1", 12, 3000, 0.02, 0.05, 0.5, "ok"),
            ExperimentOutcome("n2", 12, 2500, 0.01, 0.03, 0.4, "ok"),
            ExperimentOutcome("n3", 12, 1800, 0.008, 0.02, 0.35, "hard"),
        ]
    )

    assert result["winners"] == ["n1"]
    assert "n3" in result["kill_list"]
