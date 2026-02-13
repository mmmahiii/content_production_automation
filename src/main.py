"""Entrypoint contract for the content production automation orchestrator.

This module provides a runnable orchestrator with local adapters suitable for
runbook operations and dry-run/local execution.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Callable, Protocol, TYPE_CHECKING
from uuid import uuid4

from instagram_ai_system.adaptive_cycle import AdaptiveCycleCoordinator, AdaptiveLoopFlags
from instagram_ai_system.config import OptimizationConfig
from instagram_ai_system.experiment_lifecycle_management import ExperimentLifecycleManager
from instagram_ai_system.experiment_optimizer import ExperimentOptimizer
from instagram_ai_system.learning_strategy_updates import LearningLoopUpdater, ObjectiveAwareStrategyUpdater
from instagram_ai_system.mode_controller import ModeController
from instagram_ai_system.monetization_analytics import MonetizationAnalyst
from instagram_ai_system.production_loop import PipelineWorker, run_daily_pipeline
from instagram_ai_system.shadow_testing import ShadowTestEvaluator

if TYPE_CHECKING:
    from instagram_ai_system.storage import Database


@dataclass
class RunConfig:
    mode: str  # dry-run | local | production
    once: bool = False
    interval_seconds: int = 900
    topic: str | None = None


class TrendSource(Protocol):
    def fetch_signals(self, topic: str | None) -> dict: ...


class CreativeEngine(Protocol):
    def generate_candidates(self, signals: dict) -> list[dict]: ...


class PolicyGuard(Protocol):
    def validate(self, candidates: list[dict]) -> list[dict]: ...


class Publisher(Protocol):
    def publish(self, approved: list[dict], dry_run: bool) -> list[dict]: ...


class Analytics(Protocol):
    def collect(self, published: list[dict]) -> dict: ...


class LocalTrendSource:
    """Deterministic trend source for dry-run/local orchestration."""

    def fetch_signals(self, topic: str | None) -> dict:
        inferred_topic = topic or "general"
        return {
            "topic": inferred_topic,
            "trends": [
                {"keyword": f"{inferred_topic} quick tips", "score": 0.93},
                {"keyword": f"{inferred_topic} mistakes", "score": 0.81},
                {"keyword": f"{inferred_topic} tools", "score": 0.74},
            ],
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }


class LocalCreativeEngine:
    """Generate creative candidates from trend signals."""

    def generate_candidates(self, signals: dict) -> list[dict]:
        topic = signals.get("topic", "general")
        return [
            {
                "id": f"candidate-{i + 1}",
                "title": f"{trend['keyword'].title()} in 30 seconds",
                "hook": f"Stop scrolling: {topic} insight #{i + 1}",
                "format": "reel",
            }
            for i, trend in enumerate(signals.get("trends", []))
        ]


class LocalPolicyGuard:
    """Simple validation policy for local execution."""

    blocked_terms = {"banned", "unsafe"}

    def validate(self, candidates: list[dict]) -> list[dict]:
        approved: list[dict] = []
        for candidate in candidates:
            title = str(candidate.get("title", "")).lower()
            if any(term in title for term in self.blocked_terms):
                continue
            approved.append(candidate)
        return approved


class LocalPublisher:
    """Publisher adapter that simulates output for dry-run/local modes."""

    def publish(self, approved: list[dict], dry_run: bool) -> list[dict]:
        mode = "simulated" if dry_run else "local"
        return [
            {
                "post_id": f"{mode}-{item['id']}",
                "candidate_id": item["id"],
                "status": "published" if not dry_run else "simulated",
                "published_at": datetime.now(timezone.utc).isoformat(),
            }
            for item in approved
        ]


class LocalAnalytics:
    """Analytics adapter with deterministic local KPI estimates."""

    def collect(self, published: list[dict]) -> dict:
        published_count = len(published)
        simulated_count = sum(1 for item in published if item["status"] == "simulated")
        return {
            "reach_estimate": published_count * 1000,
            "engagement_estimate": round(published_count * 0.07, 3),
            "simulated_count": simulated_count,
        }


def _setup_logger() -> logging.Logger:
    logger = logging.getLogger("orchestrator")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    return logger


def _log_event(logger: logging.Logger, *, level: str, event: str, trace_id: str, **payload: object) -> None:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "trace_id": trace_id,
        **payload,
    }
    log_method = getattr(logger, level, logger.info)
    log_method(json.dumps(record, sort_keys=True))


def _create_db() -> "Database":
    from instagram_ai_system.storage import Base, Database

    database_url = os.getenv("DATABASE_URL", "sqlite+pysqlite:///./automation.db")
    db = Database(database_url)
    Base.metadata.create_all(db.engine)
    return db


def run_cycle(
    config: RunConfig,
    trend_source: TrendSource,
    creative_engine: CreativeEngine,
    policy_guard: PolicyGuard,
    publisher: Publisher,
    analytics: Analytics,
    *,
    adaptive_cycle: AdaptiveCycleCoordinator | None = None,
    logger: logging.Logger | None = None,
) -> dict:
    active_logger = logger or _setup_logger()
    trace_id = str(uuid4())
    _log_event(active_logger, level="info", event="cycle.started", trace_id=trace_id, mode=config.mode)

    steps = [
        ("fetch-signals", lambda: trend_source.fetch_signals(config.topic)),
        ("generate-candidates", lambda: creative_engine.generate_candidates(signals)),
        ("validate-candidates", lambda: policy_guard.validate(candidates)),
        ("publish", lambda: publisher.publish(approved, dry_run=(config.mode == "dry-run"))),
        ("collect-analytics", lambda: analytics.collect(publish_results)),
        (
            "adaptive-loop-updates",
            lambda: adaptive_cycle.process_after_analytics(metrics, trace_id=trace_id) if adaptive_cycle else {},
        ),
    ]

    try:
        for step_name, step_fn in steps:
            _log_event(active_logger, level="info", event="step.started", trace_id=trace_id, step=step_name)
            value = step_fn()
            size = len(value) if hasattr(value, "__len__") else None
            _log_event(active_logger, level="info", event="step.succeeded", trace_id=trace_id, step=step_name, size=size)

            if step_name == "fetch-signals":
                signals = value
            elif step_name == "generate-candidates":
                candidates = value
            elif step_name == "validate-candidates":
                approved = value
            elif step_name == "publish":
                publish_results = value
            elif step_name == "collect-analytics":
                metrics = value
            elif step_name == "adaptive-loop-updates":
                adaptive_updates = value

    except Exception as exc:
        _log_event(active_logger, level="error", event="step.failed", trace_id=trace_id, step=step_name, error=str(exc))
        raise

    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trace_id": trace_id,
        "mode": config.mode,
        "signals_count": len(signals),
        "candidates_count": len(candidates),
        "approved_count": len(approved),
        "published_count": len(publish_results),
        "metrics": metrics,
        "adaptive_updates": adaptive_updates,
    }
    _log_event(active_logger, level="info", event="cycle.succeeded", trace_id=trace_id, summary=summary)
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run content production automation orchestrator")
    parser.add_argument("--mode", choices=["dry-run", "local", "production"], default="dry-run")
    parser.add_argument("--once", action="store_true", help="Run exactly one cycle")
    parser.add_argument("--interval-seconds", type=int, default=900, help="Cycle sleep interval for continuous mode")
    parser.add_argument("--topic", default=None, help="Optional topic override")
    parser.add_argument("--ops", choices=["health-check", "refill-queue", "replay-failed", "kpi-report", "enqueue-daily", "run-worker"], default=None)
    parser.add_argument("--window-hours", type=int, default=24, help="Window for refill-queue operation")
    parser.add_argument("--since-hours", type=int, default=24, help="Window for replay-failed operation")
    parser.add_argument("--period", default="daily", choices=["daily", "weekly"], help="Period for kpi-report")
    return parser


def _aggregate_kpis(period: str, snapshots: list) -> dict:
    total_posts = len({snap.publish_attempt_id for snap in snapshots})
    aggregate = {"reach": 0, "shares": 0, "saves": 0, "watch_through": 0.0}
    per_post: dict[str, dict[str, float]] = {}

    for snap in snapshots:
        payload = snap.metrics_payload or {}
        attempt_id = snap.publish_attempt_id
        post = per_post.setdefault(attempt_id, {"reach": 0, "shares": 0, "saves": 0, "watch_through": 0.0, "samples": 0})
        post["reach"] += int(payload.get("reach", payload.get("views", 0)) or 0)
        post["shares"] += int(payload.get("shares", 0) or 0)
        post["saves"] += int(payload.get("saves", 0) or 0)
        post["watch_through"] += float(payload.get("watch_through", payload.get("retention", 0.0)) or 0.0)
        post["samples"] += 1

    for post in per_post.values():
        aggregate["reach"] += int(post["reach"])
        aggregate["shares"] += int(post["shares"])
        aggregate["saves"] += int(post["saves"])
        aggregate["watch_through"] += float(post["watch_through"] / max(1, post["samples"]))

    aggregate["watch_through"] = round(aggregate["watch_through"] / max(1, total_posts), 4)
    share_rate = round(aggregate["shares"] / max(1, aggregate["reach"]), 4)
    save_rate = round(aggregate["saves"] / max(1, aggregate["reach"]), 4)
    anomaly_flags = []
    if aggregate["watch_through"] < 0.3:
        anomaly_flags.append("low_watch_through")
    if share_rate < 0.01:
        anomaly_flags.append("low_share_rate")

    return {
        "period": period,
        "totals": aggregate,
        "objective_metrics": {"share_rate": share_rate, "save_rate": save_rate, "watch_through": aggregate["watch_through"]},
        "per_post": [
            {
                "publish_attempt_id": pid,
                "reach": int(m["reach"]),
                "shares": int(m["shares"]),
                "saves": int(m["saves"]),
                "watch_through": round(float(m["watch_through"]) / max(1, m["samples"]), 4),
            }
            for pid, m in per_post.items()
        ],
        "aggregate_window": {"samples": len(snapshots), "posts": total_posts},
        "anomaly_flags": anomaly_flags,
    }


def _run_ops(args: argparse.Namespace, *, logger: logging.Logger) -> dict:
    from sqlalchemy import select, text

    from instagram_ai_system.storage import OperationRunRepository, PerformanceSnapshotRepository, PublishAttemptRepository
    from instagram_ai_system.storage.models import PerformanceSnapshotModel, PublishAttemptModel

    trace_id = str(uuid4())
    started_at = datetime.now(timezone.utc)
    params_payload = {
        "mode": args.mode,
        "window_hours": args.window_hours,
        "since_hours": args.since_hours,
        "period": args.period,
    }
    db = None
    run_id = str(uuid4())

    _log_event(logger, level="info", event="ops.started", trace_id=trace_id, operation=args.ops)

    try:
        db = _create_db()
    except Exception as exc:
        if args.ops == "health-check":
            response = {
                "status": "degraded",
                "mode": args.mode,
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "dependencies": {"database": "unavailable"},
                "error": str(exc),
            }
            _log_event(logger, level="warning", event="ops.degraded", trace_id=trace_id, operation=args.ops, result=response)
            return response
        raise

    with db.session_scope() as session:
        run_repo = OperationRunRepository(session)
        run_repo.create_run(
            run_id=run_id,
            operation_name=args.ops,
            params_payload=params_payload,
            status="running",
            result_payload={},
            trace_id=trace_id,
            started_at=started_at,
        )

    try:
        with db.session_scope() as session:
            run_repo = OperationRunRepository(session)
            if args.ops == "health-check":
                dependencies = {"database": "ready", "repositories": "ready"}
                status = "ok"
                try:
                    session.execute(text("SELECT 1"))
                    from instagram_ai_system.storage import OperationRunRepository, PublishAttemptRepository, PerformanceSnapshotRepository
                    _ = OperationRunRepository(session)
                    _ = PublishAttemptRepository(session)
                    _ = PerformanceSnapshotRepository(session)
                except Exception:
                    dependencies["database"] = "unavailable"
                    dependencies["repositories"] = "unavailable"
                    status = "degraded"
                response = {
                    "status": status,
                    "mode": args.mode,
                    "checked_at": datetime.now(timezone.utc).isoformat(),
                    "dependencies": dependencies,
                }
            elif args.ops == "refill-queue":
                response = {"status": "ok", "window_hours": args.window_hours, "queued_items": max(3, args.window_hours // 6)}
            elif args.ops == "replay-failed":
                attempts = PublishAttemptRepository(session)
                since = datetime.now(timezone.utc) - timedelta(hours=args.since_hours)
                failed_attempts = list(
                    session.scalars(
                        select(PublishAttemptModel)
                        .where(PublishAttemptModel.status == "failed")
                        .where(PublishAttemptModel.attempted_at >= since)
                    )
                )
                replayed = 0
                skipped = 0
                still_failed = 0
                for failed in failed_attempts:
                    child_run_id = str(uuid4())
                    run_repo.create_run(
                        run_id=child_run_id,
                        operation_name="replay-failed",
                        params_payload={"failed_run_id": failed.id, "source_operation": args.ops},
                        status="running",
                        result_payload={},
                        trace_id=trace_id,
                        started_at=datetime.now(timezone.utc),
                    )
                    if run_repo.was_replayed(failed_run_id=failed.id):
                        skipped += 1
                        run_repo.complete_run(
                            run_id=child_run_id,
                            status="succeeded",
                            result_payload={"status": "skipped", "reason": "already_replayed", "failed_run_id": failed.id},
                            completed_at=datetime.now(timezone.utc),
                        )
                        continue
                    if failed.response_payload.get("force_still_failed"):
                        still_failed += 1
                        run_repo.complete_run(
                            run_id=child_run_id,
                            status="failed",
                            result_payload={"status": "still_failed", "failed_run_id": failed.id},
                            completed_at=datetime.now(timezone.utc),
                            error_message="Replay attempt failed",
                        )
                        continue
                    attempts.create_attempt(
                        attempt_id=f"replay-{uuid4()}",
                        brief_asset_id=failed.brief_asset_id,
                        platform=failed.platform,
                        status="success",
                        attempt_number=failed.attempt_number + 1,
                        response_payload={"replayed_from": failed.id, "idempotency_key": failed.id},
                        error_message=None,
                        attempted_at=datetime.now(timezone.utc),
                        schema_version=failed.schema_version,
                        trace_id=trace_id,
                    )
                    run_repo.complete_run(
                        run_id=child_run_id,
                        status="succeeded",
                        result_payload={"status": "replayed", "failed_run_id": failed.id},
                        completed_at=datetime.now(timezone.utc),
                    )
                    replayed += 1
                response = {
                    "status": "ok",
                    "since_hours": args.since_hours,
                    "requested": len(failed_attempts),
                    "replayed": replayed,
                    "skipped": skipped,
                    "still_failed": still_failed,
                }
            elif args.ops == "enqueue-daily":
                worker = PipelineWorker()
                run_id = worker.enqueue(topic=args.topic)
                response = {"status": "queued", "run_id": run_id, "topic": args.topic or "general"}
            elif args.ops == "run-worker":
                worker = PipelineWorker()
                run_id = worker.enqueue(topic=args.topic)
                response = worker.process(run_id)
            elif args.ops == "kpi-report":
                period_hours = 24 if args.period == "daily" else 24 * 7
                since = datetime.now(timezone.utc) - timedelta(hours=period_hours)
                snapshots = list(
                    session.scalars(
                        select(PerformanceSnapshotModel).where(PerformanceSnapshotModel.captured_at >= since)
                    )
                )
                response = {"status": "ok", **_aggregate_kpis(args.period, snapshots)}
            else:
                raise ValueError(f"Unsupported operation: {args.ops}")

            run_repo.complete_run(
                run_id=run_id,
                status="succeeded",
                result_payload=response,
                completed_at=datetime.now(timezone.utc),
            )

        _log_event(logger, level="info", event="ops.succeeded", trace_id=trace_id, operation=args.ops, result=response)
        return response
    except Exception as exc:
        with db.session_scope() as session:
            OperationRunRepository(session).complete_run(
                run_id=run_id,
                status="failed",
                result_payload={"error": str(exc)},
                completed_at=datetime.now(timezone.utc),
                error_message=str(exc),
            )
        _log_event(logger, level="error", event="ops.failed", trace_id=trace_id, operation=args.ops, error=str(exc))
        raise


def run_loop(
    config: RunConfig,
    trend_source: TrendSource,
    creative_engine: CreativeEngine,
    policy_guard: PolicyGuard,
    publisher: Publisher,
    analytics: Analytics,
    adaptive_cycle: AdaptiveCycleCoordinator | None = None,
    sleep_fn: Callable[[int], None] = sleep,
    max_cycles: int | None = None,
) -> list[dict]:
    results: list[dict] = []
    while True:
        results.append(
            run_cycle(
                config=config,
                trend_source=trend_source,
                creative_engine=creative_engine,
                policy_guard=policy_guard,
                publisher=publisher,
                analytics=analytics,
                adaptive_cycle=adaptive_cycle,
            )
        )

        if config.once:
            break
        if max_cycles is not None and len(results) >= max_cycles:
            break

        sleep_fn(config.interval_seconds)

    return results


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    logger = _setup_logger()

    if args.interval_seconds <= 0:
        parser.error("--interval-seconds must be > 0")

    if args.ops:
        result = _run_ops(args, logger=logger)
        print(json.dumps(result, sort_keys=True))
        return

    if args.mode == "production" and args.once:
        print(json.dumps(run_daily_pipeline(topic=args.topic), sort_keys=True))
        return

    config = RunConfig(mode=args.mode, once=args.once, interval_seconds=args.interval_seconds, topic=args.topic)

    trend_source = LocalTrendSource()
    creative_engine = LocalCreativeEngine()
    policy_guard = LocalPolicyGuard()
    publisher = LocalPublisher()
    analytics = LocalAnalytics()
    optimization = OptimizationConfig()
    def _decision_sink(payload: dict) -> None:
        db = _create_db()
        with db.session_scope() as session:
            from instagram_ai_system.storage import DecisionLogRepository, MonetizationInsightRepository

            updates = payload.get("updates", {})
            for key, value in updates.items():
                DecisionLogRepository(session).create(
                    decision_id=f"{payload['trace_id']}:{key}",
                    run_id=payload["trace_id"],
                    decision_type=key,
                    decision_payload=value,
                    trace_id=payload["trace_id"],
                )
                if key == "monetization_analytics":
                    MonetizationInsightRepository(session).create(
                        insight_id=f"{payload['trace_id']}:monetization",
                        run_id=payload["trace_id"],
                        insight_payload=value,
                    )

    adaptive_cycle = AdaptiveCycleCoordinator(
        optimization=optimization,
        experiment_lifecycle=ExperimentLifecycleManager(optimizer=ExperimentOptimizer(optimization)),
        learning_loop=LearningLoopUpdater(),
        objective_strategy=ObjectiveAwareStrategyUpdater(),
        mode_controller=ModeController(),
        shadow_testing=ShadowTestEvaluator(),
        monetization_analyst=MonetizationAnalyst(),
        decision_sink=_decision_sink,
        flags=AdaptiveLoopFlags(
            enable_mode_controller=True,
            enable_shadow_testing=True,
            enable_monetization_analytics=True,
        ),
    )

    while True:
        summary = run_cycle(
            config=config,
            trend_source=trend_source,
            creative_engine=creative_engine,
            policy_guard=policy_guard,
            publisher=publisher,
            analytics=analytics,
            adaptive_cycle=adaptive_cycle,
            logger=logger,
        )
        print(json.dumps(summary, sort_keys=True))

        if config.once:
            break

        _log_event(logger, level="info", event="cycle.sleeping", trace_id=summary["trace_id"], interval_seconds=config.interval_seconds)
        time.sleep(config.interval_seconds)


if __name__ == "__main__":
    main()
