from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .experiment_optimizer import ArmStats, ExperimentOptimizer
from .models import PublishedPostMetrics


@dataclass(slots=True)
class LifecycleResult:
    winner: str | None
    promoted: bool
    archived: bool


class ExperimentLifecycleManager:
    """Manages variant assignment, winner promotion, and archival markers."""

    def __init__(
        self,
        optimizer: ExperimentOptimizer,
        *,
        state_repo: object | None = None,
        schema_version: str = "1.0",
    ) -> None:
        self.optimizer = optimizer
        self.state_repo = state_repo
        self.schema_version = schema_version

    @staticmethod
    def _arm_key(experiment_id: str, variant: str) -> str:
        return f"exp::{experiment_id}::{variant}"

    def assign_variant(self, experiment_id: str, variants: Iterable[str]) -> str:
        variant_list = list(variants)
        arm_choice = self.optimizer.choose_archetype(self._arm_key(experiment_id, item) for item in variant_list)
        return arm_choice.split("::")[-1]

    def register_outcome(self, experiment_id: str, variant: str, metrics: PublishedPostMetrics) -> float:
        return self.optimizer.register_result(self._arm_key(experiment_id, variant), metrics)

    def promote_winner(
        self,
        experiment_id: str,
        variants: Iterable[str],
        *,
        min_sample_size_for_winner: int,
    ) -> LifecycleResult:
        arm_state = self.optimizer.export_arm_state()
        candidates: list[tuple[str, ArmStats]] = []
        for variant in variants:
            key = self._arm_key(experiment_id, variant)
            if key not in arm_state:
                continue
            stats = arm_state[key]
            if stats.pulls >= min_sample_size_for_winner:
                candidates.append((variant, stats))

        if not candidates:
            return LifecycleResult(winner=None, promoted=False, archived=False)

        winner, winner_stats = max(candidates, key=lambda item: item[1].avg_reward)
        self._persist_marker(
            arm_key=f"winner::{experiment_id}::{winner}",
            pulls=winner_stats.pulls,
            reward_sum=winner_stats.avg_reward,
        )
        return LifecycleResult(winner=winner, promoted=True, archived=False)

    def archive_experiment(self, experiment_id: str, *, trace_id: str) -> None:
        self._persist_marker(arm_key=f"archive::{experiment_id}", pulls=1, reward_sum=0.0, trace_id=trace_id)

    def _persist_marker(self, arm_key: str, pulls: int, reward_sum: float, trace_id: str = "system") -> None:
        if self.state_repo is None:
            return
        record = self.state_repo.build_arm_state_record(
            arm_key=arm_key,
            pulls=pulls,
            reward_sum=reward_sum,
            schema_version=self.schema_version,
            trace_id=trace_id,
        )
        self.state_repo.upsert_arm_states([record], schema_version=self.schema_version, trace_id=trace_id)
