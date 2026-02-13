from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from main import RunConfig, _format_output, _run_ops, main, run_cycle, run_loop

try:
    import sqlalchemy  # noqa: F401

    HAS_SQLALCHEMY = True
except Exception:
    HAS_SQLALCHEMY = False


@dataclass
class RecordingPublisher:
    calls: list[bool]

    def publish(self, approved: list[dict], dry_run: bool) -> list[dict]:
        self.calls.append(dry_run)
        return [{"id": item["id"], "published": not dry_run} for item in approved]


class RetryingTrendSource:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_signals(self, topic: str | None) -> dict:
        self.calls += 1
        if self.calls == 1:
            # Simulate adapter-level transient failure + retry logic.
            return self.fetch_signals(topic)
        return {"topic": topic or "default", "signals": [1, 2, 3]}


class DeterministicCreativeEngine:
    def generate_candidates(self, signals: dict) -> list[dict]:
        return [
            {"id": "c1", "signal_count": len(signals.get("signals", []))},
            {"id": "c2", "signal_count": len(signals.get("signals", []))},
        ]


class RejectingPolicyGuard:
    def validate(self, candidates: list[dict]) -> list[dict]:
        return []


class FirstOnlyPolicyGuard:
    def validate(self, candidates: list[dict]) -> list[dict]:
        return candidates[:1]


class DeterministicAnalytics:
    def collect(self, published: list[dict]) -> dict:
        return {
            "published_ids": [item["id"] for item in published],
            "ingestion_errors": 1 if published else 0,
        }


def test_run_cycle_dry_run_with_policy_rejection() -> None:
    trend = RetryingTrendSource()
    creative = DeterministicCreativeEngine()
    publisher = RecordingPublisher(calls=[])

    result = run_cycle(
        config=RunConfig(mode="dry-run", once=True, topic="ai"),
        trend_source=trend,
        creative_engine=creative,
        policy_guard=RejectingPolicyGuard(),
        publisher=publisher,
        analytics=DeterministicAnalytics(),
    )

    assert trend.calls == 2
    assert result["mode"] == "dry-run"
    assert result["approved_count"] == 0
    assert result["published_count"] == 0
    assert result["metrics"]["ingestion_errors"] == 0
    assert publisher.calls == [True]
    assert result["adaptive_updates"] == {}


def test_run_loop_once_path_runs_single_cycle_without_sleep() -> None:
    sleep_calls: list[int] = []
    results = run_loop(
        config=RunConfig(mode="local", once=True, interval_seconds=5),
        trend_source=RetryingTrendSource(),
        creative_engine=DeterministicCreativeEngine(),
        policy_guard=FirstOnlyPolicyGuard(),
        publisher=RecordingPublisher(calls=[]),
        analytics=DeterministicAnalytics(),
        sleep_fn=lambda sec: sleep_calls.append(sec),
    )

    assert len(results) == 1
    assert results[0]["published_count"] == 1
    assert sleep_calls == []


def test_run_loop_repeated_path_stops_at_max_cycles_and_sleeps_between_cycles() -> None:
    sleep_calls: list[int] = []
    publisher = RecordingPublisher(calls=[])

    results = run_loop(
        config=RunConfig(mode="production", once=False, interval_seconds=7),
        trend_source=RetryingTrendSource(),
        creative_engine=DeterministicCreativeEngine(),
        policy_guard=FirstOnlyPolicyGuard(),
        publisher=publisher,
        analytics=DeterministicAnalytics(),
        sleep_fn=lambda sec: sleep_calls.append(sec),
        max_cycles=2,
    )

    assert len(results) == 2
    assert [r["published_count"] for r in results] == [1, 1]
    assert publisher.calls == [False, False]
    assert sleep_calls == [7]


def test_run_cycle_partial_ingestion_metrics_surface_without_breaking_cycle() -> None:
    result = run_cycle(
        config=RunConfig(mode="local", once=True, topic=None),
        trend_source=RetryingTrendSource(),
        creative_engine=DeterministicCreativeEngine(),
        policy_guard=FirstOnlyPolicyGuard(),
        publisher=RecordingPublisher(calls=[]),
        analytics=DeterministicAnalytics(),
    )

    assert result["approved_count"] == 1
    assert result["published_count"] == 1
    assert result["metrics"]["ingestion_errors"] == 1


def test_format_output_summary_for_kpi_report() -> None:
    summary = _format_output(
        {
            "ops": "kpi-report",
            "status": "ok",
            "period": "daily",
            "totals": {"reach": 1000, "shares": 10, "saves": 5, "watch_through": 0.4},
            "objective_metrics": {"watch_through": 0.4},
            "aggregate_window": {"samples": 3, "posts": 1},
        },
        "summary",
    )

    assert "== Automation Summary ==" in summary
    assert "Operation: kpi-report" in summary
    assert "Reach: 1000" in summary


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy required")
def test_ops_replay_failed_uses_persisted_attempts_and_is_idempotent(tmp_path) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'ops.db'}"
    os.environ["DATABASE_URL"] = db_url

    from instagram_ai_system.storage import Base, Database, PublishAttemptRepository

    db = Database(db_url)
    Base.metadata.create_all(db.engine)
    with db.session_scope() as session:
        PublishAttemptRepository(session).create_attempt(
            attempt_id="failed-1",
            brief_asset_id="asset-1",
            platform="instagram",
            status="failed",
            attempt_number=1,
            response_payload={},
            error_message="network",
            attempted_at=datetime.now(timezone.utc),
            schema_version="1.0",
            trace_id="trace-a",
        )

    args = argparse.Namespace(
        ops="replay-failed",
        mode="local",
        window_hours=24,
        since_hours=24,
        period="daily",
        window=None,
        platform=None,
    )
    first = _run_ops(args, logger=logging.getLogger("test"))
    second = _run_ops(args, logger=logging.getLogger("test"))

    assert first["requested"] == 1
    assert first["replayed"] == 1
    assert second["skipped"] >= 1


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy required")
def test_ops_kpi_report_aggregates_from_snapshots_with_filters(tmp_path) -> None:
    db_url = f"sqlite+pysqlite:///{tmp_path / 'kpi.db'}"
    os.environ["DATABASE_URL"] = db_url

    from instagram_ai_system.storage import Base, Database, PerformanceSnapshotRepository, PublishAttemptRepository

    db = Database(db_url)
    Base.metadata.create_all(db.engine)
    now = datetime.now(timezone.utc)
    with db.session_scope() as session:
        attempts = PublishAttemptRepository(session)
        attempts.create_attempt(
            attempt_id="a1",
            brief_asset_id="asset-1",
            platform="instagram",
            status="success",
            attempt_number=1,
            response_payload={},
            error_message=None,
            attempted_at=now,
            schema_version="1.0",
            trace_id="trace-1",
        )
        attempts.create_attempt(
            attempt_id="a2",
            brief_asset_id="asset-2",
            platform="tiktok",
            status="success",
            attempt_number=1,
            response_payload={},
            error_message=None,
            attempted_at=now,
            schema_version="1.0",
            trace_id="trace-2",
        )

        repo = PerformanceSnapshotRepository(session)
        repo.record_snapshot(
            snapshot_id="s1",
            publish_attempt_id="a1",
            window="24h",
            metrics_payload={"reach": 1000, "shares": 25, "saves": 10, "watch_through": 0.41},
            derived_rates={},
            captured_at=now,
            schema_version="1.0",
            trace_id="trace-1",
        )
        repo.record_snapshot(
            snapshot_id="s2",
            publish_attempt_id="a2",
            window="7d",
            metrics_payload={"reach": 9000, "shares": 1, "saves": 1, "watch_through": 0.2},
            derived_rates={},
            captured_at=now,
            schema_version="1.0",
            trace_id="trace-2",
        )

    args = argparse.Namespace(
        ops="kpi-report",
        mode="local",
        window_hours=24,
        since_hours=24,
        period="daily",
        window="24h",
        platform="instagram",
    )
    result = _run_ops(args, logger=logging.getLogger("test"))

    assert result["totals"]["reach"] == 1000
    assert result["objective_metrics"]["share_rate"] == 0.025
    assert result["filters"] == {"window": "24h", "platform": "instagram"}


@pytest.mark.skipif(not HAS_SQLALCHEMY, reason="sqlalchemy required")
def test_health_check_degraded_when_database_unavailable(monkeypatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///./nonexistent_dir/ops.db")
    args = argparse.Namespace(
        ops="health-check",
        mode="local",
        window_hours=24,
        since_hours=24,
        period="daily",
        window=None,
        platform=None,
    )
    result = _run_ops(args, logger=logging.getLogger("test"))
    assert result["status"] == "degraded"
    assert result["dependencies"]["database"] == "unavailable"


def test_main_summary_output_mode(monkeypatch, capsys) -> None:
    class StubAdaptiveCycle:
        def __init__(self, **_: object) -> None:
            pass

        def process_after_analytics(self, metrics: dict, trace_id: str) -> dict:
            return {}

    monkeypatch.setattr("main.AdaptiveCycleCoordinator", StubAdaptiveCycle)
    monkeypatch.setattr(
        "sys.argv",
        ["main.py", "--mode", "dry-run", "--once", "--output", "summary"],
    )
    main()
    out = capsys.readouterr().out
    assert "== Automation Summary ==" in out
    assert "Mode: dry-run" in out


def test_main_json_output_mode(monkeypatch, capsys) -> None:
    class StubAdaptiveCycle:
        def __init__(self, **_: object) -> None:
            pass

        def process_after_analytics(self, metrics: dict, trace_id: str) -> dict:
            return {}

    monkeypatch.setattr("main.AdaptiveCycleCoordinator", StubAdaptiveCycle)
    monkeypatch.setattr(
        "sys.argv",
        ["main.py", "--mode", "dry-run", "--once", "--output", "json"],
    )
    main()
    out = capsys.readouterr().out.strip()
    parsed = json.loads(out)
    assert parsed["mode"] == "dry-run"
