"""Entrypoint contract for the content production automation orchestrator.

This module provides a runnable orchestrator with local adapters suitable for
runbook operations and dry-run/local execution.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from dataclasses import dataclass
from time import sleep
from datetime import datetime, timezone
from typing import Callable, Protocol
from uuid import uuid4

from instagram_ai_system.adaptive_cycle import AdaptiveCycleCoordinator, AdaptiveLoopFlags
from instagram_ai_system.config import OptimizationConfig
from instagram_ai_system.experiment_lifecycle_management import ExperimentLifecycleManager
from instagram_ai_system.experiment_optimizer import ExperimentOptimizer
from instagram_ai_system.learning_strategy_updates import LearningLoopUpdater, ObjectiveAwareStrategyUpdater


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
    """Execute one orchestration cycle.

    Sequence contract:
      1) Fetch trend/performance signals.
      2) Generate candidate content variants.
      3) Validate against safety/policy/quality constraints.
      4) Publish approved assets (or simulate in dry-run).
      5) Collect KPI outputs and return cycle summary.
    """

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

    context: dict[str, object] = {}

    try:
        for step_name, step_fn in steps:
            _log_event(active_logger, level="info", event="step.started", trace_id=trace_id, step=step_name)
            value = step_fn()
            context[step_name] = value
            size = len(value) if hasattr(value, "__len__") else None
            _log_event(
                active_logger,
                level="info",
                event="step.succeeded",
                trace_id=trace_id,
                step=step_name,
                size=size,
            )

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
        _log_event(
            active_logger,
            level="error",
            event="step.failed",
            trace_id=trace_id,
            step=step_name,
            error=str(exc),
        )
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

    parser.add_argument(
        "--ops",
        choices=["health-check", "refill-queue", "replay-failed", "kpi-report"],
        default=None,
        help="Runbook operations command",
    )
    parser.add_argument("--window-hours", type=int, default=24, help="Window for refill-queue operation")
    parser.add_argument("--since-hours", type=int, default=24, help="Window for replay-failed operation")
    parser.add_argument("--period", default="daily", choices=["daily", "weekly"], help="Period for kpi-report")
    return parser


def _run_ops(args: argparse.Namespace, *, logger: logging.Logger) -> dict:
    trace_id = str(uuid4())
    _log_event(logger, level="info", event="ops.started", trace_id=trace_id, operation=args.ops)

    if args.ops == "health-check":
        response = {"status": "ok", "mode": args.mode, "checked_at": datetime.now(timezone.utc).isoformat()}
    elif args.ops == "refill-queue":
        response = {"status": "ok", "window_hours": args.window_hours, "queued_items": max(3, args.window_hours // 6)}
    elif args.ops == "replay-failed":
        response = {"status": "ok", "since_hours": args.since_hours, "replayed_jobs": max(0, args.since_hours // 8)}
    elif args.ops == "kpi-report":
        response = {
            "status": "ok",
            "period": args.period,
            "kpis": {"reach": 12000 if args.period == "daily" else 84000, "shares": 310 if args.period == "daily" else 2170},
        }
    else:
        raise ValueError(f"Unsupported operation: {args.ops}")

    _log_event(logger, level="info", event="ops.succeeded", trace_id=trace_id, operation=args.ops, result=response)
    return response


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
    """Run one or many cycles based on configuration.

    Args:
        max_cycles: Optional loop guard for tests and controlled runs.
    """

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

    config = RunConfig(
        mode=args.mode,
        once=args.once,
        interval_seconds=args.interval_seconds,
        topic=args.topic,
    )

    trend_source = LocalTrendSource()
    creative_engine = LocalCreativeEngine()
    policy_guard = LocalPolicyGuard()
    publisher = LocalPublisher()
    analytics = LocalAnalytics()
    optimization = OptimizationConfig()
    adaptive_cycle = AdaptiveCycleCoordinator(
        optimization=optimization,
        experiment_lifecycle=ExperimentLifecycleManager(optimizer=ExperimentOptimizer(optimization)),
        learning_loop=LearningLoopUpdater(),
        objective_strategy=ObjectiveAwareStrategyUpdater(),
        flags=AdaptiveLoopFlags(),
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

        _log_event(
            logger,
            level="info",
            event="cycle.sleeping",
            trace_id=summary["trace_id"],
            interval_seconds=config.interval_seconds,
        )
        time.sleep(config.interval_seconds)


if __name__ == "__main__":
    main()
