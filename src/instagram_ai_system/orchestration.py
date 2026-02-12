from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Iterable, List
from uuid import uuid4

from .config import OptimizationConfig, PageStrategyConfig
from .content_factory import ContentFactory, FactoryRequest
from .creativity_engine import CreativityEngine
from .experiment_optimizer import ArmStats, ExperimentOptimizer
from .models import ContentBrief, PublishedPostMetrics, ReelSignal
from .trend_intelligence import TrendIntelligenceEngine

if TYPE_CHECKING:
    from .storage.repositories import ExperimentStateRepository


@dataclass(slots=True)
class CycleOutput:
    selected_briefs: List[ContentBrief]
    top_patterns: List[str]


class InstagramAISystem:
    """Main coordinator for trend mining, creation, and optimization."""

    def __init__(
        self,
        strategy: PageStrategyConfig,
        optimization: OptimizationConfig | None = None,
        experiment_state_repo: ExperimentStateRepository | None = None,
    ) -> None:
        self.strategy = strategy
        self.optimization = optimization or OptimizationConfig()
        self.trend_engine = TrendIntelligenceEngine()
        self.creativity_engine = CreativityEngine()
        self.factory = ContentFactory(self.creativity_engine)
        self.optimizer = ExperimentOptimizer(self.optimization)
        self.experiment_state_repo = experiment_state_repo
        self._brief_to_archetype: Dict[str, str] = {}

        self._load_optimizer_state()

    def _load_optimizer_state(self) -> None:
        if self.experiment_state_repo is None:
            return

        state_map = {
            row.arm_key: ArmStats(pulls=row.pulls, reward_sum=row.reward_sum)
            for row in self.experiment_state_repo.load_arm_states()
        }
        self.optimizer.import_arm_state(state_map)

    def _persist_optimizer_state(self, trace_id: str | None = None) -> None:
        if self.experiment_state_repo is None:
            return

        state_rows = []
        for arm_key, stats in self.optimizer.export_arm_state().items():
            state_rows.append(
                self.experiment_state_repo.build_arm_state_record(
                    arm_key=arm_key,
                    pulls=stats.pulls,
                    reward_sum=stats.reward_sum,
                    schema_version="1.0",
                    trace_id=trace_id or str(uuid4()),
                )
            )

        self.experiment_state_repo.upsert_arm_states(
            state_rows,
            schema_version="1.0",
            trace_id=trace_id or str(uuid4()),
        )

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

    def register_post_metrics(self, metrics: PublishedPostMetrics, trace_id: str | None = None) -> float:
        archetype = self._brief_to_archetype.get(metrics.brief_id, "problem_solution")
        reward = self.optimizer.register_result(archetype, metrics)
        self._persist_optimizer_state(trace_id=trace_id)
        return reward
