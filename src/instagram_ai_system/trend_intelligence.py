from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Iterable, List

from .models import ReelSignal, TrendInsight


class TrendIntelligenceEngine:
    """Extract viral patterns from observed reels."""

    def extract_top_patterns(self, signals: Iterable[ReelSignal], limit: int = 10) -> List[TrendInsight]:
        by_hook = defaultdict(list)
        by_duration = defaultdict(list)

        for signal in signals:
            virality_proxy = self._virality_proxy(signal)
            by_hook[signal.hook_style].append(virality_proxy)
            duration_bucket = self._duration_bucket(signal.duration_seconds)
            by_duration[duration_bucket].append(virality_proxy)

        insights: List[TrendInsight] = []
        for hook_style, values in by_hook.items():
            insights.append(
                TrendInsight(
                    pattern=f"hook:{hook_style}",
                    score=mean(values),
                    rationale=f"Average virality proxy for hook '{hook_style}' from {len(values)} reels.",
                )
            )

        for duration_bucket, values in by_duration.items():
            insights.append(
                TrendInsight(
                    pattern=f"duration:{duration_bucket}",
                    score=mean(values),
                    rationale=f"Average virality proxy for {duration_bucket} duration from {len(values)} reels.",
                )
            )

        insights.sort(key=lambda i: i.score, reverse=True)
        return insights[:limit]

    @staticmethod
    def _virality_proxy(signal: ReelSignal) -> float:
        retention = mean(signal.retention_curve) if signal.retention_curve else 0
        engagement = signal.shares * 3 + signal.saves * 3 + signal.comments * 2
        novelty = signal.visual_novelty_score * 100
        audio = signal.audio_trend_score * 100
        return retention * 100 + engagement + novelty + audio

    @staticmethod
    def _duration_bucket(duration_seconds: float) -> str:
        if duration_seconds < 10:
            return "0-9s"
        if duration_seconds < 20:
            return "10-19s"
        if duration_seconds < 35:
            return "20-34s"
        return "35s+"
