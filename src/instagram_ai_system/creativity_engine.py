from __future__ import annotations

from dataclasses import dataclass
from random import choice, randint
from typing import Iterable, List
from uuid import uuid4

from .models import ContentBrief, CreativityMode, TrendInsight


@dataclass(slots=True)
class CreativityGuardrails:
    banned_topics: List[str]
    mandatory_disclosures: List[str]


class CreativityEngine:
    """Generates content concepts with configurable creativity levels."""

    def __init__(self, guardrails: CreativityGuardrails | None = None) -> None:
        self.guardrails = guardrails or CreativityGuardrails(
            banned_topics=["medical misinformation", "hate speech", "illegal activity"],
            mandatory_disclosures=["This content is AI-assisted."],
        )

    def generate_brief(
        self,
        niche: str,
        persona: str,
        mode: CreativityMode,
        trend_insights: Iterable[TrendInsight],
    ) -> ContentBrief:
        top_patterns = [ins.pattern for ins in list(trend_insights)[:4]]
        topic = self._topic_for_mode(niche, mode)
        hook = self._hook_for_mode(mode, top_patterns)
        storyboard = self._storyboard_for_mode(topic, mode)
        caption = self._caption(topic, persona, mode)

        return ContentBrief(
            brief_id=str(uuid4()),
            topic=topic,
            hook=hook,
            storyboard=storyboard,
            caption=caption,
            cta="Comment the word 'template' and I'll send the framework.",
            hashtags=self._hashtags(niche, mode),
            creativity_mode=mode,
            target_persona=persona,
            trend_references=top_patterns,
        )

    @staticmethod
    def _topic_for_mode(niche: str, mode: CreativityMode) -> str:
        if mode == CreativityMode.SAFE:
            return f"3 practical {niche} tactics you can use today"
        if mode == CreativityMode.BALANCED:
            return f"Unpopular {niche} strategy that works in 2026"
        return f"Experimental {niche} challenge: build results in {randint(24, 72)} hours"

    @staticmethod
    def _hook_for_mode(mode: CreativityMode, patterns: List[str]) -> str:
        anchors = ", ".join(patterns[:2]) if patterns else "high-retention hooks"
        if mode == CreativityMode.FULL:
            return f"I ignored all standard advice and this happened ({anchors})"
        if mode == CreativityMode.BALANCED:
            return f"Most creators miss this hidden signal ({anchors})"
        return f"If you're stuck, start with this simple framework ({anchors})"

    @staticmethod
    def _storyboard_for_mode(topic: str, mode: CreativityMode) -> List[str]:
        base = [
            f"Scene 1: Pattern interrupt with on-screen text: '{topic}'",
            "Scene 2: Demonstrate the method visually in 3 beats",
            "Scene 3: Show before/after with explicit metric",
            "Scene 4: CTA with next action",
        ]
        if mode == CreativityMode.FULL:
            base.insert(2, "Scene X: Surprising twist or contrarian reveal")
        return base

    def _caption(self, topic: str, persona: str, mode: CreativityMode) -> str:
        intensity = {
            CreativityMode.SAFE: "step-by-step",
            CreativityMode.BALANCED: "evidence-backed",
            CreativityMode.FULL: "high-risk, high-reward",
        }[mode]
        disclosure = self.guardrails.mandatory_disclosures[0]
        return f"{persona}: this is a {intensity} breakdown of {topic}. Save this and test it today. {disclosure}"

    @staticmethod
    def _hashtags(niche: str, mode: CreativityMode) -> List[str]:
        universal = ["#creator", "#growth", "#instagramtips"]
        niche_tag = f"#{niche.lower().replace(' ', '')}"
        mode_tag = {
            CreativityMode.SAFE: "#practical",
            CreativityMode.BALANCED: "#strategy",
            CreativityMode.FULL: "#creativeexperiment",
        }[mode]
        return [niche_tag, mode_tag, *universal]
