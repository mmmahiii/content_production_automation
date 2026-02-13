from __future__ import annotations

from dataclasses import dataclass

from main import RunConfig, run_cycle, run_loop


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
    assert result["adaptive_updates"] == {}
