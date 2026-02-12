from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable
from uuid import uuid4

from .schema_validation import validate_payload

_ALLOWED_NICHES = {
    "personal productivity and self-improvement",
    "fitness and body recomposition",
    "personal finance basics",
}


@dataclass(slots=True)
class IdeaGenerationRequest:
    niche: str
    sub_topics: list[str] | None = None
    tone_preference: str = "educational"
    count: int = 10


class IdeaGenerationService:
    schema_path = "contracts/idea_generation.schema.json"

    def generate(self, request: IdeaGenerationRequest) -> dict:
        niche_normalized = request.niche.strip().lower()
        if niche_normalized not in _ALLOWED_NICHES:
            raise ValueError("Unsupported niche for MVP.")
        if request.count < 10:
            raise ValueError("At least 10 ideas are required.")

        sub_topics = request.sub_topics or ["foundations", "mistakes", "quick wins"]
        ideas = [
            self._build_idea(niche=request.niche, tone=request.tone_preference, sub_topic=sub_topics[i % len(sub_topics)], rank=i + 1)
            for i in range(request.count)
        ]
        payload = {
            "request_id": str(uuid4()),
            "niche": request.niche,
            "tone_preference": request.tone_preference,
            "idea_count": len(ideas),
            "ideas": ideas,
        }
        validate_payload(payload, self.schema_path)
        return payload

    def _build_idea(self, niche: str, tone: str, sub_topic: str, rank: int) -> dict:
        hooks = self._dedupe_hooks(
            [
                f"Stop scrolling: the {sub_topic} mistake costing you progress.",
                f"Nobody tells you this {sub_topic} shortcut in {niche}.",
                f"If you only fix one thing in {sub_topic}, fix this today.",
                f"A {tone} rethink: {sub_topic} is easier than you think.",
            ]
        )
        return {
            "idea_id": f"idea-{uuid4()}",
            "rank": rank,
            "title": f"{sub_topic.title()} system for {niche}",
            "premise": f"Teach a repeatable {sub_topic} framework with one fast example.",
            "audience_pain_or_desire": f"Wants clear wins in {sub_topic} without wasting time.",
            "hook_options": hooks[:3],
            "thumbnail_text_options": [f"{sub_topic.title()} reset", "Do this today"],
            "caption_direction": f"Use a {tone} tone with one actionable checklist and save-focused CTA.",
        }

    @staticmethod
    def _dedupe_hooks(hooks: Iterable[str]) -> list[str]:
        unique: list[str] = []
        for hook in hooks:
            if not hook.strip():
                continue
            if all(SequenceMatcher(None, hook, existing).ratio() < 0.8 for existing in unique):
                unique.append(hook)
        return unique
