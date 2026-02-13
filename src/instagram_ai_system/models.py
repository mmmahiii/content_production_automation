from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List


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


@dataclass(slots=True)
class NicheCandidate:
    niche_name: str
    target_audience: str
    content_formats: List[str]
    unique_angle: str
    example_post_ideas: List[str]
    creator_persona_tone: str
    production_requirements: List[str]
    monetization_routes: List[str]


@dataclass(slots=True)
class NicheScoreBreakdown:
    niche_name: str
    demand: float
    low_saturation: float
    feasibility: float
    differentiation_space: float
    monetization: float
    success_score: float
    top_risks: List[str] = field(default_factory=list)


@dataclass(slots=True)
class ExperimentPlan:
    niche_name: str
    account_handle: str
    cadence_per_week: int
    planned_posts: int
    content_format_mix: List[str]


@dataclass(slots=True)
class ExperimentOutcome:
    niche_name: str
    posts_published: int
    median_views: float
    follow_conversion_rate: float
    saves_shares_per_view: float
    retention_proxy: float
    feasibility_note: str


@dataclass(slots=True)
class DecisionReport:
    generated_at: datetime
    ranked_niches: List[NicheScoreBreakdown]
    portfolio_plan: List[ExperimentPlan]
    recommended_posting_plan: Dict[str, Any]
