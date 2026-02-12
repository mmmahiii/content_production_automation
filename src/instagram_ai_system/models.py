from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List


class CreativityMode(str, Enum):
    SAFE = "safe"
    BALANCED = "balanced"
    FULL = "full"


@dataclass(slots=True)
class ReelSignal:
    reel_id: str
    niche: str
    hook_style: str
    duration_seconds: float
    caption_length: int
    audio_trend_score: float
    visual_novelty_score: float
    retention_curve: List[float]
    shares: int
    saves: int
    comments: int
    posted_at: datetime


@dataclass(slots=True)
class TrendInsight:
    pattern: str
    score: float
    rationale: str


@dataclass(slots=True)
class ContentBrief:
    brief_id: str
    topic: str
    hook: str
    storyboard: List[str]
    caption: str
    cta: str
    hashtags: List[str]
    creativity_mode: CreativityMode
    target_persona: str
    trend_references: List[str] = field(default_factory=list)


@dataclass(slots=True)
class PublishedPostMetrics:
    brief_id: str
    views: int
    likes: int
    comments: int
    shares: int
    saves: int
    avg_watch_time_seconds: float

    def score(self, weights: Dict[str, float]) -> float:
        return (
            self.views * weights.get("views", 0)
            + self.likes * weights.get("likes", 0)
            + self.comments * weights.get("comments", 0)
            + self.shares * weights.get("shares", 0)
            + self.saves * weights.get("saves", 0)
            + self.avg_watch_time_seconds * weights.get("watch_time", 0)
        )
