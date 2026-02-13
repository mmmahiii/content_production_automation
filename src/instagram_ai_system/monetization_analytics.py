from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MonetizationInsight:
    monetization_score: float
    growth_score: float
    total_objective: float
    drift_flag: bool


class MonetizationAnalyst:
    def evaluate(
        self,
        *,
        metrics: dict[str, float],
        weights: tuple[float, float] = (0.65, 0.35),
        intent_baseline: float = 0.03,
    ) -> MonetizationInsight:
        wg, wm = weights
        views = float(metrics.get("views", 0.0))
        shares = float(metrics.get("shares", 0.0))
        saves = float(metrics.get("saves", 0.0))
        intent = float(metrics.get("intent_comments", 0.0))
        profile_actions = float(metrics.get("profile_actions", 0.0))

        growth = min(1.0, ((shares + saves) / max(1.0, views)) * 8.0)
        monetization = min(1.0, ((intent + profile_actions) / max(1.0, views)) * 12.0)
        total = wg * growth + wm * monetization
        drift_flag = (intent / max(1.0, views)) < intent_baseline and growth > 0.4
        return MonetizationInsight(
            monetization_score=round(monetization, 4),
            growth_score=round(growth, 4),
            total_objective=round(total, 4),
            drift_flag=drift_flag,
        )
