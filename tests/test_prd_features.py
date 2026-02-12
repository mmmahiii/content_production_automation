from datetime import datetime, timedelta, timezone

from instagram_ai_system.idea_generation import IdeaGenerationRequest, IdeaGenerationService
from instagram_ai_system.performance_ingestion import PerformanceIngestionService
from instagram_ai_system.scheduling_metadata import SchedulingMetadataService, SchedulingRequest
from instagram_ai_system.script_generation import ScriptGenerationRequest, ScriptGenerationService


def test_idea_script_schedule_pipeline() -> None:
    idea_service = IdeaGenerationService()
    ideas_payload = idea_service.generate(
        IdeaGenerationRequest(
            niche="personal productivity and self-improvement",
            sub_topics=["focus", "planning"],
            tone_preference="educational",
            count=10,
        )
    )
    assert ideas_payload["idea_count"] == 10

    script_service = ScriptGenerationService()
    script = script_service.generate(
        ScriptGenerationRequest(
            idea=ideas_payload["ideas"][0],
            duration_seconds=30,
            tone="educational",
            cta_preference="Comment PLAN for the checklist",
        )
    )
    assert script["source_idea_id"] == ideas_payload["ideas"][0]["idea_id"]

    scheduler = SchedulingMetadataService()
    now = datetime.now(timezone.utc)
    schedule = scheduler.generate(
        SchedulingRequest(
            script_packages=[script for _ in range(7)],
            date_start=now,
            date_end=now + timedelta(days=15),
            timezone="UTC",
            cadence="daily",
        )
    )
    assert len(schedule["items"]) == 7


def test_performance_ingestion_csv_and_json() -> None:
    service = PerformanceIngestionService()
    csv_payload = """post_id,observed_at,window,impressions,plays,avg_watch_time,likes,comments,shares,saves,follower_change
post-1,2026-01-01T00:00:00+00:00,24h,1000,500,18.5,45,3,20,25,5
post-2,,24h,1000,0,0,2,1,0,0,0
"""
    csv_result = service.ingest_csv(csv_payload)
    assert csv_result.summary == {"processed": 2, "succeeded": 1, "failed": 1}
    assert csv_result.errors[0]["row"] == 2

    json_result = service.ingest_json(
        [
            {
                "post_id": "post-1",
                "observed_at": "2026-01-08T00:00:00+00:00",
                "window": "7d",
                "impressions": 2000,
                "plays": 1000,
                "avg_watch_time": 20,
                "likes": 100,
                "comments": 10,
                "shares": 35,
                "saves": 40,
                "follower_change": 15,
            }
        ]
    )
    assert json_result.summary == {"processed": 1, "succeeded": 1, "failed": 0}
    queried = service.query(
        post_id="post-1",
        start=datetime.fromisoformat("2026-01-01T00:00:00+00:00"),
        end=datetime.fromisoformat("2026-01-31T00:00:00+00:00"),
    )
    assert len(queried) == 2
