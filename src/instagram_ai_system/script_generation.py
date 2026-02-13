from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from .contracts_envelope import coerce_to_envelope, extract_payload
from .schema_validation import validate_payload

_DURATION_BUCKETS = {15: (12, 18), 30: (24, 36), 45: (36, 54)}


@dataclass(slots=True)
class ScriptGenerationRequest:
    idea: dict
    duration_seconds: int
    tone: str
    cta_preference: str


class ScriptGenerationService:
    schema_path = "contracts/script_package.schema.json"

    def generate(self, request: ScriptGenerationRequest) -> dict:
        if request.duration_seconds not in _DURATION_BUCKETS:
            raise ValueError("Duration bucket must be one of 15/30/45 seconds.")
        idea = extract_payload(request.idea)
        idea_id = idea.get("idea_id")
        if not idea_id:
            raise ValueError("idea payload must contain idea_id")

        hook_seconds = max(3, int(request.duration_seconds * 0.2))
        cta_seconds = max(3, int(request.duration_seconds * 0.2))
        body_seconds = request.duration_seconds - hook_seconds - cta_seconds
        payload = {
            "script_id": f"script-{uuid4()}",
            "source_idea_id": idea_id,
            "duration_bucket_seconds": request.duration_seconds,
            "estimated_total_duration_seconds": hook_seconds + body_seconds + cta_seconds,
            "segments": [
                {
                    "segment_type": "hook",
                    "start_second": 0,
                    "end_second": hook_seconds,
                    "voiceover": idea["hook_options"][0],
                    "on_screen_text": "You are doing this wrong",
                },
                {
                    "segment_type": "body",
                    "start_second": hook_seconds,
                    "end_second": hook_seconds + body_seconds,
                    "voiceover": idea["premise"],
                    "on_screen_text": "Step 1, Step 2, Step 3",
                },
                {
                    "segment_type": "cta",
                    "start_second": hook_seconds + body_seconds,
                    "end_second": hook_seconds + body_seconds + cta_seconds,
                    "voiceover": request.cta_preference,
                    "on_screen_text": "Save and share for later",
                },
            ],
            "caption_variants": {
                "short": f"{idea['title']}. Save this for your next sprint.",
                "long": f"{idea['premise']}\n\nTone: {request.tone}.\nCTA: {request.cta_preference}",
            },
            "hashtags": [
                "#instagramreels",
                "#contentstrategy",
                "#creatorgrowth",
                "#socialmediatips",
                "#reelstips",
            ],
        }
        min_duration, max_duration = _DURATION_BUCKETS[request.duration_seconds]
        if not (min_duration <= payload["estimated_total_duration_seconds"] <= max_duration):
            raise ValueError("Generated script violates duration tolerance.")
        enveloped_payload = coerce_to_envelope(payload)
        validate_payload(enveloped_payload, self.schema_path)
        return enveloped_payload
