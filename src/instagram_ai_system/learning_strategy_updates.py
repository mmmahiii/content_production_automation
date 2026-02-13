from __future__ import annotations

from dataclasses import dataclass

from .config import OptimizationConfig


@dataclass(slots=True)
class LearningLoopUpdate:
    sample_count: int
    mean_error: float
    mean_absolute_error: float


class LearningLoopUpdater:
    """Updates optimizer exploration pressure using observed-vs-predicted errors."""

    def apply(self, *, observed: list[float], predicted: list[float], optimization: OptimizationConfig) -> LearningLoopUpdate:
        pairs = list(zip(observed, predicted, strict=False))
        if not pairs:
            return LearningLoopUpdate(sample_count=0, mean_error=0.0, mean_absolute_error=0.0)

        errors = [obs - pred for obs, pred in pairs]
        mean_error = sum(errors) / len(errors)
        mae = sum(abs(err) for err in errors) / len(errors)

        # If estimates are noisy, expand exploration safely.
        if mae > 0.15:
            optimization.epsilon_exploration = min(0.5, optimization.epsilon_exploration + 0.05)
        elif mae < 0.05:
            optimization.epsilon_exploration = max(0.05, optimization.epsilon_exploration - 0.02)

        return LearningLoopUpdate(sample_count=len(errors), mean_error=mean_error, mean_absolute_error=mae)


@dataclass(slots=True)
class StrategyUpdate:
    objective: str
    adjusted_weights: dict[str, float]


class ObjectiveAwareStrategyUpdater:
    """Adjusts objective weights based on KPI deltas with bounded shifts."""

    KPI_TO_WEIGHT = {
        "reach_delta": "views",
        "engagement_delta": "likes",
        "conversation_delta": "comments",
        "share_delta": "shares",
        "save_delta": "saves",
        "watch_time_delta": "watch_time",
    }

    def apply(
        self,
        *,
        objective: str,
        kpi_deltas: dict[str, float],
        optimization: OptimizationConfig,
        adjustment_step: float = 0.03,
    ) -> StrategyUpdate:
        weights = dict(optimization.objective_weights)
        for delta_key, value in kpi_deltas.items():
            metric_key = self.KPI_TO_WEIGHT.get(delta_key)
            if metric_key is None:
                continue
            direction = -1 if value < 0 else 1
            weights[metric_key] = max(0.01, weights.get(metric_key, 0.01) + (adjustment_step * direction))

        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        optimization.objective_weights = weights
        return StrategyUpdate(objective=objective, adjusted_weights=weights)
