from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from random import choice, random
from typing import Dict, Iterable

from .config import OptimizationConfig
from .models import PublishedPostMetrics


@dataclass(slots=True)
class ArmStats:
    pulls: int = 0
    reward_sum: float = 0.0

    @property
    def avg_reward(self) -> float:
        return self.reward_sum / self.pulls if self.pulls else 0.0


class ExperimentOptimizer:
    """Simple epsilon-greedy optimizer over content archetypes."""

    def __init__(self, config: OptimizationConfig):
        self.config = config
        self.arms: Dict[str, ArmStats] = defaultdict(ArmStats)

    def choose_archetype(self, candidates: Iterable[str]) -> str:
        candidates = list(candidates)
        unseen = [c for c in candidates if self.arms[c].pulls == 0]
        if unseen:
            return choice(unseen)

        if random() < self.config.epsilon_exploration:
            return choice(candidates)

        return max(candidates, key=lambda c: self.arms[c].avg_reward)

    def register_result(self, archetype: str, metrics: PublishedPostMetrics) -> float:
        reward = metrics.score(self.config.objective_weights)
        stats = self.arms[archetype]
        stats.pulls += 1
        stats.reward_sum += reward
        return reward

    def export_arm_state(self) -> dict[str, ArmStats]:
        return {name: ArmStats(pulls=stats.pulls, reward_sum=stats.reward_sum) for name, stats in self.arms.items()}

    def import_arm_state(self, arm_state: dict[str, ArmStats]) -> None:
        for name, stats in arm_state.items():
            state = self.arms[name]
            state.pulls = stats.pulls
            state.reward_sum = stats.reward_sum
