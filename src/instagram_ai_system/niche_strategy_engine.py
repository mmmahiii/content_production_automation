from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Iterable

from .models import (
    DecisionReport,
    ExperimentOutcome,
    ExperimentPlan,
    NicheCandidate,
    NicheScoreBreakdown,
)


@dataclass(slots=True)
class SuccessScoreWeights:
    demand: float = 0.25
    low_saturation: float = 0.20
    feasibility: float = 0.20
    differentiation_space: float = 0.15
    monetization: float = 0.20


class NicheStrategyEngine:
    """Ranks niche candidates and emits an auditable experimentation portfolio."""

    def __init__(self, weights: SuccessScoreWeights | None = None) -> None:
        self.weights = weights or SuccessScoreWeights()
        self._model_version = "rules-v1"

    def generate_candidates(
        self,
        *,
        seed_categories: Iterable[str],
        constraints: dict[str, Any] | None = None,
        variants_per_seed: int = 4,
    ) -> list[NicheCandidate]:
        constraints = constraints or {}
        candidates: list[NicheCandidate] = []
        for seed in seed_categories:
            for idx in range(variants_per_seed):
                niche_name = f"{seed.strip()} - angle {idx + 1}"
                candidates.append(
                    NicheCandidate(
                        niche_name=niche_name,
                        target_audience=f"{seed.strip()} practitioners seeking fast wins",
                        content_formats=["short reel", "carousel", "story Q&A"],
                        unique_angle=f"Evidence-backed {seed.strip()} workflows under constraints: {constraints or 'none'}",
                        example_post_ideas=[
                            f"{seed.strip()} teardown #{i + 1}" for i in range(10)
                        ],
                        creator_persona_tone="operator-led, practical, no-hype",
                        production_requirements=[
                            "screen recording",
                            "caption templates",
                            "weekly trend scan",
                        ],
                        monetization_routes=["affiliate", "templates", "sponsorship", "micro-course"],
                    )
                )
        return candidates

    def collect_signals(self, candidates: Iterable[NicheCandidate]) -> dict[str, dict[str, float]]:
        signals: dict[str, dict[str, float]] = {}
        for candidate in candidates:
            basis = max(1, len(candidate.niche_name))
            signals[candidate.niche_name] = {
                "demand": min(1.0, 0.45 + (basis % 11) / 20),
                "saturation": min(1.0, 0.25 + (basis % 9) / 12),
                "differentiation_space": min(1.0, 0.3 + (basis % 7) / 10),
                "feasibility": 0.7 if len(candidate.production_requirements) <= 4 else 0.5,
                "monetization": 0.6 + min(0.35, len(candidate.monetization_routes) * 0.05),
                "production_complexity": 0.35,
                "compliance_risk": 0.2,
                "asset_dependency": 0.25,
            }
        return signals

    def score_candidates(
        self,
        candidates: Iterable[NicheCandidate],
        signals: dict[str, dict[str, float]],
    ) -> list[NicheScoreBreakdown]:
        scored: list[NicheScoreBreakdown] = []
        for candidate in candidates:
            signal = signals[candidate.niche_name]
            low_saturation = 1 - signal["saturation"]
            success_score = (
                self.weights.demand * signal["demand"]
                + self.weights.low_saturation * low_saturation
                + self.weights.feasibility * signal["feasibility"]
                + self.weights.differentiation_space * signal["differentiation_space"]
                + self.weights.monetization * signal["monetization"]
            )
            top_risks = []
            if signal["saturation"] > 0.65:
                top_risks.append("high_saturation")
            if signal["compliance_risk"] > 0.4:
                top_risks.append("compliance_exposure")
            if signal["asset_dependency"] > 0.5:
                top_risks.append("asset_dependency")
            scored.append(
                NicheScoreBreakdown(
                    niche_name=candidate.niche_name,
                    demand=signal["demand"],
                    low_saturation=low_saturation,
                    feasibility=signal["feasibility"],
                    differentiation_space=signal["differentiation_space"],
                    monetization=signal["monetization"],
                    success_score=round(success_score, 4),
                    top_risks=top_risks,
                )
            )
        return sorted(scored, key=lambda row: row.success_score, reverse=True)

    def select_portfolio(self, ranked: list[NicheScoreBreakdown], top_k: int = 5) -> list[ExperimentPlan]:
        picks = ranked[:top_k]
        portfolio: list[ExperimentPlan] = []
        for index, niche in enumerate(picks, start=1):
            portfolio.append(
                ExperimentPlan(
                    niche_name=niche.niche_name,
                    account_handle=f"@pilot_{index}_{niche.niche_name.lower().replace(' ', '_')[:18]}",
                    cadence_per_week=5,
                    planned_posts=12,
                    content_format_mix=["short reel", "carousel", "story"],
                )
            )
        return portfolio

    def evaluate_results(self, performance_snapshots: Iterable[ExperimentOutcome]) -> dict[str, Any]:
        snapshots = list(performance_snapshots)
        if not snapshots:
            return {"winners": [], "kill_list": [], "summary": {"count": 0}}

        ranked = sorted(
            snapshots,
            key=lambda row: (
                row.follow_conversion_rate,
                row.saves_shares_per_view,
                row.retention_proxy,
                row.median_views,
            ),
            reverse=True,
        )
        winner_count = max(1, round(len(ranked) * 0.4))
        winners = [row.niche_name for row in ranked[:winner_count]]
        kill_list = [row.niche_name for row in ranked[winner_count:]]
        return {
            "winners": winners,
            "kill_list": kill_list,
            "summary": {
                "count": len(ranked),
                "median_follow_conversion": round(mean(row.follow_conversion_rate for row in ranked), 4),
                "median_retention_proxy": round(mean(row.retention_proxy for row in ranked), 4),
            },
        }

    def update_model(self) -> dict[str, str]:
        self._model_version = "rules-v1"
        return {"model_version": self._model_version, "status": "ready_for_learning_phase"}

    def build_decision_report(
        self,
        ranked: list[NicheScoreBreakdown],
        portfolio: list[ExperimentPlan],
    ) -> DecisionReport:
        return DecisionReport(
            generated_at=datetime.now(timezone.utc),
            ranked_niches=ranked,
            portfolio_plan=portfolio,
            recommended_posting_plan={
                "phase": "stage-1-portfolio-test",
                "posts_per_niche": 12,
                "cadence_per_week": 5,
                "kill_threshold": "bottom_60_percent",
            },
        )
