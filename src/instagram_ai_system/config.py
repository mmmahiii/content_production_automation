from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .models import CreativityMode


@dataclass(slots=True)
class PageStrategyConfig:
    niche: str
    target_personas: List[str]
    posting_times_utc: List[str]
    max_posts_per_day: int = 3
    creativity_mode: CreativityMode = CreativityMode.BALANCED


@dataclass(slots=True)
class OptimizationConfig:
    objective_weights: Dict[str, float] = field(
        default_factory=lambda: {
            "views": 0.10,
            "likes": 0.15,
            "comments": 0.20,
            "shares": 0.25,
            "saves": 0.25,
            "watch_time": 0.05,
        }
    )
    epsilon_exploration: float = 0.2
    min_sample_size_for_winner: int = 20
