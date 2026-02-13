from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ShadowVariantResult:
    variant_id: str
    views: int
    saves: int
    shares: int
    comments: int
    confidence: float


@dataclass(slots=True)
class ShadowWinner:
    winner_variant_id: str | None
    ranked: list[dict[str, Any]]
    deferred: bool


class ShadowTestEvaluator:
    def evaluate(self, results: list[ShadowVariantResult], *, min_views: int = 200) -> ShadowWinner:
        if not results:
            return ShadowWinner(winner_variant_id=None, ranked=[], deferred=True)

        ranked = []
        for r in results:
            primary = (r.saves + r.shares) / max(1, r.views)
            secondary = r.comments / max(1, r.views)
            score = primary * 0.8 + secondary * 0.2
            ranked.append(
                {
                    "variant_id": r.variant_id,
                    "views": r.views,
                    "primary_metric": round(primary, 4),
                    "secondary_metric": round(secondary, 4),
                    "weighted_score": round(score, 4),
                    "confidence": r.confidence,
                }
            )

        ranked.sort(key=lambda item: item["weighted_score"], reverse=True)
        top = ranked[0]
        defer = top["views"] < min_views or top["confidence"] < 0.65
        return ShadowWinner(
            winner_variant_id=None if defer else top["variant_id"],
            ranked=ranked,
            deferred=defer,
        )
