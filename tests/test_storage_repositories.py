from __future__ import annotations

from datetime import datetime

import pytest

pytest.importorskip("sqlalchemy")

from instagram_ai_system import CreativityMode, PageStrategyConfig, PublishedPostMetrics, ReelSignal
from instagram_ai_system.orchestration import InstagramAISystem
from instagram_ai_system.storage import (
    Base,
    BriefAssetRepository,
    ContentPlanRepository,
    Database,
    ExperimentStateRepository,
    PerformanceSnapshotRepository,
    PublishAttemptRepository,
    OperationRunRepository,
)


def test_repositories_round_trip_records() -> None:
    db = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(db.engine)

    with db.session_scope() as session:
        plans = ContentPlanRepository(session)
        briefs = BriefAssetRepository(session)
        attempts = PublishAttemptRepository(session)
        snapshots = PerformanceSnapshotRepository(session)

        plans.upsert_plan(
            plan_id="plan-1",
            topic="ai productivity",
            objective="engagement",
            status="queued",
            payload={"slots": ["09:00"]},
            schema_version="1.0",
            trace_id="trace-1",
        )
        briefs.create_brief_asset(
            asset_id="asset-1",
            content_plan_id="plan-1",
            brief_payload={"hook": "Use this"},
            asset_payload={"caption": "Caption"},
            lifecycle_state="approved",
            schema_version="1.0",
            trace_id="trace-1",
        )
        attempts.create_attempt(
            attempt_id="attempt-1",
            brief_asset_id="asset-1",
            platform="instagram",
            status="success",
            attempt_number=1,
            response_payload={"post_id": "p1"},
            error_message=None,
            attempted_at=datetime.utcnow(),
            schema_version="1.0",
            trace_id="trace-2",
        )
        snapshots.record_snapshot(
            snapshot_id="snap-1",
            publish_attempt_id="attempt-1",
            window="24h",
            metrics_payload={"views": 1000, "likes": 50},
            derived_rates={"like_rate": 0.05},
            captured_at=datetime.utcnow(),
            schema_version="1.0",
            trace_id="trace-3",
        )

    with db.session_scope() as session:
        plan = ContentPlanRepository(session).get_plan("plan-1")
        assert plan is not None
        assert plan.schema_version == "1.0"
        assert BriefAssetRepository(session).list_for_plan("plan-1")
        assert PublishAttemptRepository(session).list_for_asset("asset-1")
        assert PerformanceSnapshotRepository(session).list_for_attempt("attempt-1")


def test_optimizer_state_persists_across_system_restarts() -> None:
    db = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(db.engine)

    strategy = PageStrategyConfig(
        niche="AI Marketing",
        target_personas=["founders"],
        posting_times_utc=["12:00"],
        max_posts_per_day=1,
        creativity_mode=CreativityMode.BALANCED,
    )

    with db.session_scope() as session:
        repo = ExperimentStateRepository(session)
        system = InstagramAISystem(strategy=strategy, experiment_state_repo=repo)
        system.run_creation_cycle(
            [
                ReelSignal(
                    reel_id="r1",
                    niche="ai marketing",
                    hook_style="curiosity_gap",
                    duration_seconds=10,
                    caption_length=100,
                    audio_trend_score=0.6,
                    visual_novelty_score=0.7,
                    retention_curve=[0.9, 0.8],
                    shares=15,
                    saves=10,
                    comments=5,
                    posted_at=datetime.utcnow(),
                )
            ]
        )
        system.register_post_metrics(
            PublishedPostMetrics(
                brief_id="unknown-brief",
                views=100,
                likes=10,
                comments=2,
                shares=1,
                saves=1,
                avg_watch_time_seconds=8,
            ),
            trace_id="trace-persist",
        )

    with db.session_scope() as session:
        repo = ExperimentStateRepository(session)
        restored = InstagramAISystem(strategy=strategy, experiment_state_repo=repo)
        assert restored.optimizer.arms["problem_solution"].pulls == 1
        assert restored.optimizer.arms["problem_solution"].reward_sum > 0


def test_operation_run_repository_tracks_failed_and_replayed_state() -> None:
    db = Database("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(db.engine)

    now = datetime.utcnow()
    with db.session_scope() as session:
        repo = OperationRunRepository(session)
        repo.create_run(
            run_id="run-1",
            operation_name="publish",
            params_payload={"asset_id": "a1"},
            status="failed",
            result_payload={"error": "timeout"},
            trace_id="trace-1",
            started_at=now,
            completed_at=now,
            error_message="timeout",
        )
        repo.create_run(
            run_id="run-2",
            operation_name="replay-failed",
            params_payload={"failed_run_id": "run-1"},
            status="succeeded",
            result_payload={"status": "replayed"},
            trace_id="trace-2",
            started_at=now,
            completed_at=now,
        )

    with db.session_scope() as session:
        repo = OperationRunRepository(session)
        failed = repo.list_failed_runs(operation_name="publish", since=datetime(2000, 1, 1))
        assert len(failed) == 1
        assert failed[0].id == "run-1"
        assert repo.was_replayed(failed_run_id="run-1") is True
