from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .config import OptimizationConfig, PageStrategyConfig
from .content_factory import ContentFactory, FactoryRequest
from .creativity_engine import CreativityEngine
from .experiment_optimizer import ExperimentOptimizer
from .models import ContentBrief, PublishedPostMetrics, ReelSignal
from .trend_intelligence import TrendIntelligenceEngine


@dataclass(slots=True)
class CycleOutput:
    selected_briefs: List[ContentBrief]
    top_patterns: List[str]


class InstagramAISystem:
    """Main coordinator for trend mining, creation, and optimization."""

    def __init__(self, strategy: PageStrategyConfig, optimization: OptimizationConfig | None = None) -> None:
        self.strategy = strategy
        self.optimization = optimization or OptimizationConfig()
        self.trend_engine = TrendIntelligenceEngine()
        self.creativity_engine = CreativityEngine()
        self.factory = ContentFactory(self.creativity_engine)
        self.optimizer = ExperimentOptimizer(self.optimization)
        self._brief_to_archetype: Dict[str, str] = {}

    def run_creation_cycle(self, observed_reels: Iterable[ReelSignal]) -> CycleOutput:
        insights = self.trend_engine.extract_top_patterns(observed_reels, limit=8)
        selected_briefs: List[ContentBrief] = []

        archetypes = [
            "problem_solution",
            "contrarian_take",
            "case_study_breakdown",
            "challenge_format",
        ]

        for persona in self.strategy.target_personas:
            request = FactoryRequest(
                niche=self.strategy.niche,
                persona=persona,
                creativity_mode=self.strategy.creativity_mode,
                batch_size=2,
            )
            batch = self.factory.build_batch(request, insights)

            for brief in batch:
                archetype = self.optimizer.choose_archetype(archetypes)
                brief.caption += f" Archetype: {archetype.replace('_', ' ')}."
                self._brief_to_archetype[brief.brief_id] = archetype
                selected_briefs.append(brief)

        return CycleOutput(
            selected_briefs=selected_briefs[: self.strategy.max_posts_per_day],
            top_patterns=[ins.pattern for ins in insights[:5]],
        )

    def register_post_metrics(self, metrics: PublishedPostMetrics) -> float:
        archetype = self._brief_to_archetype.get(metrics.brief_id, "problem_solution")
        return self.optimizer.register_result(archetype, metrics)
