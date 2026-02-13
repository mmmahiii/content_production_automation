from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .config import OptimizationConfig
from .experiment_lifecycle_management import ExperimentLifecycleManager
from .learning_strategy_updates import LearningLoopUpdater, ObjectiveAwareStrategyUpdater
from .mode_controller import ModeController, ModeInputs
from .monetization_analytics import MonetizationAnalyst
from .shadow_testing import ShadowTestEvaluator, ShadowVariantResult


@dataclass(slots=True)
class AdaptiveLoopFlags:
    enable_experiment_lifecycle: bool = False
    enable_learning_loop: bool = False
    enable_objective_strategy: bool = False
    enable_mode_controller: bool = False
    enable_shadow_testing: bool = False
    enable_monetization_analytics: bool = False


class AdaptiveCycleCoordinator:
    """Integration point for adaptive loops between analytics and planning."""

    def __init__(
        self,
        *,
        optimization: OptimizationConfig,
        experiment_lifecycle: ExperimentLifecycleManager,
        learning_loop: LearningLoopUpdater,
        objective_strategy: ObjectiveAwareStrategyUpdater,
        mode_controller: ModeController | None = None,
        shadow_testing: ShadowTestEvaluator | None = None,
        monetization_analyst: MonetizationAnalyst | None = None,
        decision_sink: Callable[[dict], None] | None = None,
        flags: AdaptiveLoopFlags | None = None,
    ) -> None:
        self.optimization = optimization
        self.experiment_lifecycle = experiment_lifecycle
        self.learning_loop = learning_loop
        self.objective_strategy = objective_strategy
        self.mode_controller = mode_controller or ModeController()
        self.shadow_testing = shadow_testing or ShadowTestEvaluator()
        self.monetization_analyst = monetization_analyst or MonetizationAnalyst()
        self.decision_sink = decision_sink
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

        if self.flags.enable_shadow_testing:
            raw_results = analytics_payload.get("shadow_test_results") or []
            results = [ShadowVariantResult(**row) for row in raw_results if isinstance(row, dict)]
            shadow = self.shadow_testing.evaluate(results)
            updates["shadow_testing"] = {
                "winner_variant_id": shadow.winner_variant_id,
                "deferred": shadow.deferred,
                "ranked": shadow.ranked,
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

        if self.flags.enable_mode_controller:
            mode_inputs = ModeInputs(**(analytics_payload.get("mode_inputs") or {
                "hit_rate_7d": 0.5,
                "novelty_fatigue": 0.5,
                "account_volatility": 0.3,
                "confidence_trend": 0.0,
                "monetization_drift": 0.0,
                "plateau_cycles": 0,
                "hours_since_mode_change": 12,
                "drawdown_24h": 0.0,
                "risk_budget": 0.5,
            }))
            decision = self.mode_controller.decide(
                current_mode=str(analytics_payload.get("current_mode", "exploit")),
                explore_coef=float(analytics_payload.get("explore_coef", self.optimization.epsilon_exploration)),
                inputs=mode_inputs,
            )
            self.optimization.epsilon_exploration = decision.explore_coef
            updates["mode_controller"] = {
                "mode": decision.mode,
                "explore_coef": decision.explore_coef,
                "rationale": decision.rationale,
            }

        if self.flags.enable_monetization_analytics:
            insight = self.monetization_analyst.evaluate(metrics=analytics_payload.get("monetization_metrics") or {})
            updates["monetization_analytics"] = {
                "growth_score": insight.growth_score,
                "monetization_score": insight.monetization_score,
                "total_objective": insight.total_objective,
                "drift_flag": insight.drift_flag,
            }

        if self.decision_sink and updates:
            self.decision_sink({"trace_id": trace_id, "updates": updates})

        return updates
