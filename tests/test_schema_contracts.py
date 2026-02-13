from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")
from jsonschema import Draft202012Validator, FormatChecker

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
    "contracts/idea_generation.schema.json": {
        "schema_version": "1.0",
        "trace_id": "trace-idea-1",
        "created_at": "2026-01-01T00:00:00Z",
        "payload": {
            "request_id": "req-1",
            "niche": "ai-marketing",
            "tone_preference": "contrarian",
            "idea_count": 10,
            "ideas": [
                {
                    "idea_id": f"idea-{idx}",
                    "rank": idx,
                    "title": f"Idea title {idx}",
                    "premise": f"Premise for idea {idx}",
                    "audience_pain_or_desire": "Need repeatable short-form growth",
                    "hook_options": [f"Hook {idx}-a", f"Hook {idx}-b", f"Hook {idx}-c"],
                    "thumbnail_text_options": [f"Thumb {idx}-a", f"Thumb {idx}-b"],
                    "caption_direction": "Explain framework + CTA",
                }
                for idx in range(1, 11)
            ],
        },
    },
    "contracts/script_package.schema.json": {
        "schema_version": "1.0",
        "trace_id": "trace-script-1",
        "created_at": "2026-01-01T00:00:00Z",
        "payload": {
            "script_id": "script-1",
            "source_idea_id": "idea-1",
            "duration_bucket_seconds": 30,
            "estimated_total_duration_seconds": 29.5,
            "segments": [
                {
                    "segment_type": "hook",
                    "start_second": 0,
                    "end_second": 4,
                    "voiceover": "You are one workflow away from doubling content output.",
                    "on_screen_text": "Double output with one workflow",
                },
                {
                    "segment_type": "body",
                    "start_second": 4,
                    "end_second": 22,
                    "voiceover": "Use this three-step system: collect signals, generate ideas, ship variants.",
                    "on_screen_text": "3-step system: signals -> ideas -> variants",
                },
                {
                    "segment_type": "cta",
                    "start_second": 22,
                    "end_second": 29.5,
                    "voiceover": "Save this and follow for daily creator systems.",
                    "on_screen_text": "Save + follow for daily systems",
                },
            ],
            "caption_variants": {
                "short": "3-step workflow that keeps your reel pipeline full.",
                "long": "A practical workflow to turn trend signals into scripts you can publish this week.",
            },
            "hashtags": ["#ai", "#creator", "#instagramgrowth", "#contentstrategy", "#reels"],
        },
    },
    "contracts/scheduling_metadata.schema.json": {
        "schema_version": "1.0",
        "trace_id": "trace-schedule-1",
        "created_at": "2026-01-01T00:00:00Z",
        "payload": {
            "items": [
                {
                    "schedule_id": "sch-1",
                    "script_id": "script-1",
                    "publish_datetime": "2026-01-02T15:00:00Z",
                    "timezone": "UTC",
                    "slot_label": "afternoon",
                    "kpi_objective": "reach",
                    "platform_metadata": {
                        "caption": "Ship one repeatable workflow per day.",
                        "hashtags": ["#ai", "#creator", "#instagramgrowth", "#contentstrategy", "#reels"],
                        "thumbnail_text": "Workflow that scales",
                        "hook_text": "Most creators skip this system",
                    },
                }
            ]
        },
    },
    "schemas/performance_ingestion_record.schema.json": {
        "schema_version": "1.0",
        "trace_id": "trace-perf-1",
        "created_at": "2026-01-01T00:00:00Z",
        "payload": {
            "post_id": "post-1",
            "observed_at": "2026-01-01T01:00:00Z",
            "window": "60m",
            "impressions": 1500,
            "plays": 1250,
            "avg_watch_time": 8.7,
            "likes": 90,
            "comments": 12,
            "shares": 25,
            "saves": 45,
            "follower_change": 18,
            "derived_metrics": {
                "engagement_rate": 0.115,
                "save_rate": 0.03,
                "share_rate": 0.016,
                "watch_through_estimate": 0.41,
            },
            "kpi_label": "success",
        },
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
    "schemas/niche_candidate.schema.json": {
        "nicheName": "AI Operators for Agencies",
        "targetAudience": "Agency founders",
        "contentFormats": ["short reel", "carousel"],
        "uniqueAngle": "No-face execution playbooks",
        "examplePostIdeas": ["Post 1", "Post 2", "Post 3"],
        "creatorPersonaTone": "practical",
        "productionRequirements": ["screen capture"],
        "monetizationRoutes": ["affiliate", "templates"]
    },
    "schemas/niche_score_breakdown.schema.json": {
        "nicheName": "AI Operators for Agencies",
        "demand": 0.8,
        "lowSaturation": 0.6,
        "feasibility": 0.9,
        "differentiationSpace": 0.7,
        "monetization": 0.8,
        "successScore": 0.76
    },
    "schemas/experiment_plan.schema.json": {
        "nicheName": "AI Operators for Agencies",
        "accountHandle": "@pilot_ai_ops",
        "cadencePerWeek": 5,
        "plannedPosts": 12,
        "contentFormatMix": ["short reel", "carousel"]
    },
    "schemas/experiment_outcome.schema.json": {
        "nicheName": "AI Operators for Agencies",
        "postsPublished": 12,
        "medianViews": 4200,
        "followConversionRate": 0.018,
        "savesSharesPerView": 0.062,
        "retentionProxy": 0.44,
        "feasibilityNote": "Sustainable with 2-hour daily block"
    },
}


@pytest.mark.parametrize("schema_path", sorted(VALID_PAYLOADS))
def test_valid_payloads_match_schema_contracts(schema_path: str) -> None:
    schema = json.loads((ROOT / schema_path).read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
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
        ("schemas/niche_candidate.schema.json", lambda d: d["contentFormats"].clear()),
        ("schemas/niche_score_breakdown.schema.json", lambda d: d.__setitem__("successScore", 1.2)),
        ("schemas/experiment_plan.schema.json", lambda d: d.__setitem__("plannedPosts", 0)),
        ("schemas/experiment_outcome.schema.json", lambda d: d.__setitem__("retentionProxy", 1.2)),
    ],
)
def test_invalid_payloads_are_rejected(schema_path: str, mutator) -> None:
    schema = json.loads((ROOT / schema_path).read_text())
    payload = json.loads(json.dumps(VALID_PAYLOADS[schema_path]))
    mutator(payload)

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = list(validator.iter_errors(payload))
    assert errors, f"Expected validation error for {schema_path}"


@pytest.mark.parametrize(
    ("schema_path", "mutator", "expected_field"),
    [
        ("contracts/idea_generation.schema.json", lambda d: d.pop("schema_version"), "schema_version"),
        ("contracts/script_package.schema.json", lambda d: d.pop("trace_id"), "trace_id"),
        (
            "contracts/scheduling_metadata.schema.json",
            lambda d: d.__setitem__("created_at", "2026/01/01 00:00:00"),
            "created_at",
        ),
        ("schemas/performance_ingestion_record.schema.json", lambda d: d.pop("payload"), "payload"),
    ],
)
def test_envelope_validation_errors_are_field_specific(schema_path: str, mutator, expected_field: str) -> None:
    schema = json.loads((ROOT / schema_path).read_text())
    payload = json.loads(json.dumps(VALID_PAYLOADS[schema_path]))
    mutator(payload)

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = list(validator.iter_errors(payload))

    assert errors, f"Expected envelope validation error for {schema_path}"
    messages = [error.message for error in errors]
    assert any(expected_field in message for message in messages)
