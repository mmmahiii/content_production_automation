from __future__ import annotations

from instagram_ai_system.adaptive_cycle import AdaptiveCycleCoordinator, AdaptiveLoopFlags
from instagram_ai_system.config import OptimizationConfig
from instagram_ai_system.experiment_lifecycle_management import ExperimentLifecycleManager
from instagram_ai_system.experiment_optimizer import ExperimentOptimizer
from instagram_ai_system.learning_strategy_updates import LearningLoopUpdater, ObjectiveAwareStrategyUpdater
from instagram_ai_system.models import PublishedPostMetrics


class InMemoryExperimentStateRepo:
    def __init__(self) -> None:
        self.records: dict[str, object] = {}

    class _Record:
        def __init__(self, *, arm_key: str, pulls: int, reward_sum: float, schema_version: str, trace_id: str) -> None:
            self.arm_key = arm_key
            self.pulls = pulls
            self.reward_sum = reward_sum
            self.schema_version = schema_version
            self.trace_id = trace_id

    def build_arm_state_record(self, *, arm_key: str, pulls: int, reward_sum: float, schema_version: str, trace_id: str):
        return self._Record(
            arm_key=arm_key,
            pulls=pulls,
            reward_sum=reward_sum,
            schema_version=schema_version,
            trace_id=trace_id,
        )

    def upsert_arm_states(self, arm_states, *, schema_version: str, trace_id: str) -> None:
        for state in arm_states:
            self.records[state.arm_key] = state


def test_experiment_lifecycle_promotes_winner_and_archives() -> None:
    optimization = OptimizationConfig(min_sample_size_for_winner=2)
    optimizer = ExperimentOptimizer(optimization)
    repo = InMemoryExperimentStateRepo()
    lifecycle = ExperimentLifecycleManager(optimizer=optimizer, state_repo=repo)

    high = PublishedPostMetrics("b1", 1000, 200, 50, 40, 35, 8)
    low = PublishedPostMetrics("b2", 200, 20, 5, 1, 1, 2)

    lifecycle.register_outcome("exp-1", "variant-a", high)
    lifecycle.register_outcome("exp-1", "variant-a", high)
    lifecycle.register_outcome("exp-1", "variant-b", low)
    lifecycle.register_outcome("exp-1", "variant-b", low)

    result = lifecycle.promote_winner("exp-1", ["variant-a", "variant-b"], min_sample_size_for_winner=2)
    assert result.promoted is True
    assert result.winner == "variant-a"

    lifecycle.archive_experiment("exp-1", trace_id="trace-archive")
    assert "winner::exp-1::variant-a" in repo.records
    assert "archive::exp-1" in repo.records


def test_adaptive_cycle_updates_learning_and_objective_weights() -> None:
    optimization = OptimizationConfig(epsilon_exploration=0.2)
    coordinator = AdaptiveCycleCoordinator(
        optimization=optimization,
        experiment_lifecycle=ExperimentLifecycleManager(optimizer=ExperimentOptimizer(optimization)),
        learning_loop=LearningLoopUpdater(),
        objective_strategy=ObjectiveAwareStrategyUpdater(),
        flags=AdaptiveLoopFlags(enable_learning_loop=True, enable_objective_strategy=True),
    )

    updates = coordinator.process_after_analytics(
        {
            "observed_scores": [0.9, 0.8, 0.7],
            "predicted_scores": [0.1, 0.2, 0.3],
            "objective": "engagement",
            "kpi_deltas": {"engagement_delta": -0.2, "share_delta": 0.3},
        },
        trace_id="trace-1",
    )

    assert "learning_loop" in updates
    assert updates["learning_loop"]["epsilon_exploration"] > 0.2
    assert "objective_strategy" in updates
    weights = updates["objective_strategy"]["adjusted_weights"]
    assert abs(sum(weights.values()) - 1.0) < 1e-8
