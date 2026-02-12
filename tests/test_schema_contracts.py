from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


VALID_PAYLOADS: dict[str, dict] = {
    "contracts/content_idea.schema.json": {
        "idea_id": "idea-1",
        "mode": "explore",
        "creative_brief": {"tone": "bold", "aesthetic": "minimal", "hook_direction": "contrarian"},
        "virality_score": 78.4,
        "variant_budget": 3,
    },
    "contracts/learning_update.schema.json": {
        "update_id": "u1",
        "cycle_id": "c1",
        "predicted_vs_actual_error": 0.12,
        "mode_adjustment": {"exploration_coefficient_delta": 0.1, "target_mode": "mutation"},
        "applied_at": "2026-01-01T00:00:00Z",
    },
    "contracts/variant_result.schema.json": {
        "variant_id": "v1",
        "idea_id": "i1",
        "metrics": {"views": 1200, "saves": 80, "shares": 22, "comments": 15, "velocity": 4.3},
        "observation_window_minutes": 60,
        "status": "promoted",
        "confidence": 0.86,
    },
    "contracts/virality_event.schema.json": {
        "reel_id": "r1",
        "niche": "ai",
        "hook_type": "curiosity_gap",
        "audio_id": "a22",
        "caption_style": "tutorial",
        "visual_structure": "listicle",
        "posting_time": "2026-01-01T00:00:00Z",
        "growth_curve": {"h1": 100, "h2": 220},
        "outcome_score": 92,
    },
    "schemas/content_candidate.schema.json": {
        "id": "cand-1",
        "createdAt": "2026-01-01T00:00:00Z",
        "theme": "b2b",
        "variant": "explore-a",
        "promptTemplateId": "tpl-9",
        "generationConstraints": {"duration": "30s"},
        "status": "draft",
    },
    "schemas/performance_snapshot.schema.json": {
        "id": "snap-1",
        "publishedPostId": "post-1",
        "capturedAt": "2026-01-01T00:00:00Z",
        "metrics": {
            "views": 100,
            "retention": 0.6,
            "likes": 7,
            "comments": 2,
            "shares": 1,
            "saves": 4,
            "profileVisits": 3,
        },
    },
    "schemas/published_post.schema.json": {
        "id": "post-1",
        "contentCandidateId": "cand-1",
        "platform": "instagram",
        "publishedAt": "2026-01-01T00:00:00Z",
        "url": "https://example.com/post/1",
    },
}


@pytest.mark.parametrize("schema_path", sorted(VALID_PAYLOADS))
def test_valid_payloads_match_schema_contracts(schema_path: str) -> None:
    schema = json.loads((ROOT / schema_path).read_text())
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(VALID_PAYLOADS[schema_path]))
    assert errors == []


@pytest.mark.parametrize(
    ("schema_path", "mutator"),
    [
        ("contracts/content_idea.schema.json", lambda d: d.pop("idea_id")),
        ("contracts/learning_update.schema.json", lambda d: d.__setitem__("predicted_vs_actual_error", -1)),
        ("contracts/variant_result.schema.json", lambda d: d["metrics"].pop("views")),
        ("contracts/virality_event.schema.json", lambda d: d.__setitem__("outcome_score", 101)),
        ("schemas/content_candidate.schema.json", lambda d: d.__setitem__("status", "invalid")),
        ("schemas/performance_snapshot.schema.json", lambda d: d["metrics"].__setitem__("retention", 1.5)),
        ("schemas/published_post.schema.json", lambda d: d.__setitem__("url", "not-a-uri")),
    ],
)
def test_invalid_payloads_are_rejected(schema_path: str, mutator) -> None:
    schema = json.loads((ROOT / schema_path).read_text())
    payload = json.loads(json.dumps(VALID_PAYLOADS[schema_path]))
    mutator(payload)

    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(payload))
    assert errors, f"Expected validation error for {schema_path}"
