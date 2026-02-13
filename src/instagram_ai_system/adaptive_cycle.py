from __future__ import annotations

from dataclasses import dataclass

from .config import OptimizationConfig
from .experiment_lifecycle_management import ExperimentLifecycleManager
from .learning_strategy_updates import LearningLoopUpdater, ObjectiveAwareStrategyUpdater


@dataclass(slots=True)
class AdaptiveLoopFlags:
    enable_experiment_lifecycle: bool = False
    enable_learning_loop: bool = False
    enable_objective_strategy: bool = False


class AdaptiveCycleCoordinator:
    """Integration point for adaptive loops between analytics and planning."""

    def __init__(
        self,
        *,
        optimization: OptimizationConfig,
        experiment_lifecycle: ExperimentLifecycleManager,
        learning_loop: LearningLoopUpdater,
        objective_strategy: ObjectiveAwareStrategyUpdater,
        flags: AdaptiveLoopFlags | None = None,
    ) -> None:
        self.optimization = optimization
        self.experiment_lifecycle = experiment_lifecycle
        self.learning_loop = learning_loop
        self.objective_strategy = objective_strategy
        self.flags = flags or AdaptiveLoopFlags()

    def process_after_analytics(self, analytics_payload: dict, *, trace_id: str) -> dict:
        updates: dict[str, object] = {}

        if self.flags.enable_experiment_lifecycle:
            exp = analytics_payload.get("experiment") or {}
            experiment_id = exp.get("experiment_id")
            variants = exp.get("variants") or []
            if experiment_id and variants:
                result = self.experiment_lifecycle.promote_winner(
                    experiment_id,
                    variants,
                    min_sample_size_for_winner=self.optimization.min_sample_size_for_winner,
                )
                if result.promoted and result.winner is not None:
                    self.experiment_lifecycle.archive_experiment(experiment_id, trace_id=trace_id)
                updates["experiment_lifecycle"] = {
                    "winner": result.winner,
                    "promoted": result.promoted,
                }

        if self.flags.enable_learning_loop:
            observed = analytics_payload.get("observed_scores") or []
            predicted = analytics_payload.get("predicted_scores") or []
            update = self.learning_loop.apply(observed=observed, predicted=predicted, optimization=self.optimization)
            updates["learning_loop"] = {
                "sample_count": update.sample_count,
                "mean_error": update.mean_error,
                "mean_absolute_error": update.mean_absolute_error,
                "epsilon_exploration": self.optimization.epsilon_exploration,
            }

        if self.flags.enable_objective_strategy:
            objective = str(analytics_payload.get("objective", "engagement"))
            kpi_deltas = analytics_payload.get("kpi_deltas") or {}
            strategy = self.objective_strategy.apply(
                objective=objective,
                kpi_deltas=kpi_deltas,
                optimization=self.optimization,
            )
            updates["objective_strategy"] = {
                "objective": strategy.objective,
                "adjusted_weights": strategy.adjusted_weights,
            }

        return updates
