# Content Production Automation Architecture

## 1) Purpose and Scope

This document describes the **implementation-aligned architecture** for the current codebase and maps it to the longer-term target design.

## 2) Implementation-Aligned Repository Layout (Current)

> ✅ This is the authoritative module layout for onboarding and implementation.

```text
src/
  main.py
  instagram_ai_system/
    config.py
    models.py
    trend_intelligence.py
    creativity_engine.py
    content_factory.py
    idea_generation.py
    script_generation.py
    schema_validation.py
    scheduling_metadata.py
    experiment_optimizer.py
    performance_ingestion.py
    orchestration.py
    production_loop.py
    storage/
      database.py
      models.py
      repositories.py
  integrations/
    instagram/
      publisher.py
      metrics.py
    trends/
      adapters.py
```

### Outdated structure note

The previously documented example tree below is obsolete and should not be used for implementation planning:

```text
(OUTDATED) src/content_generation, src/trend_analysis, src/scoring, src/orchestration
```

## 3) Current State vs Target State

### 3.1 Current implemented modules and responsibilities

- **Entrypoint orchestration (`src/main.py`)**
  - Defines runtime cycle contract and runbook ops commands.
  - Uses protocol interfaces for trend source, generation, policy validation, publishing, and analytics.
  - Ships local adapters for deterministic dry-run/local execution.

- **Core domain package (`src/instagram_ai_system`)**
  - `trend_intelligence.py`: extracts ranked trend insights from observed reel signals.
  - `creativity_engine.py` + `content_factory.py`: generate policy-aware content briefs and batch variants.
  - `idea_generation.py` / `script_generation.py`: structured generation services for ideas/scripts.
  - `schema_validation.py`: validates generated artifacts against canonical expectations.
  - `scheduling_metadata.py`: derives publish timing metadata.
  - `experiment_optimizer.py`: exploration/exploitation logic for archetype optimization.
  - `performance_ingestion.py`: ingests and scores published-post performance.
  - `orchestration.py`: composes trend, creativity, and optimizer services into a creation cycle.
  - `production_loop.py`: end-to-end daily worker slice (trend -> creative -> render -> publish -> metrics -> learning snapshot) with stage checkpointing and idempotent resume semantics.
  - `storage/`: database session management plus repositories/models for persisted experiment state.

- **Integration package (`src/integrations`)**
  - `instagram/publisher.py`: publish request/result contract, governance approval gate, idempotency, retries, audit entries.
  - `instagram/metrics.py`: Instagram metrics normalization and rollup helpers.
  - `trends/adapters.py`: multi-source trend adapter protocol and normalized trend model.

### 3.2 Adaptive modules implemented in current runtime

The following target-design adaptive modules now exist as implementation modules in `src/instagram_ai_system`:

- **Mode controller** (`mode_controller.py`)
  - Boundary: `ModeController.decide(current_mode, explore_coef, inputs)`
  - Contract: `ModeInputs` -> `ModeDecision`
  - Limitation: static threshold policy; no learned transition model yet.
- **Shadow testing** (`shadow_testing.py`)
  - Boundary: `ShadowTestEvaluator.evaluate(results, min_views=200)`
  - Contract: `list[ShadowVariantResult]` -> `ShadowWinner`
  - Limitation: heuristic weighted-score ranking with fixed confidence/min-view cutoffs.
- **Learning loop + objective strategy updates** (`learning_strategy_updates.py`)
  - Boundaries: `LearningLoopUpdater.apply(...)`, `ObjectiveAwareStrategyUpdater.apply(...)`
  - Contract: observed/predicted arrays + KPI delta map mutate `OptimizationConfig`, returning structured updates.
  - Limitation: in-process config mutation only; no persisted model snapshot rollback controller.
- **Monetization analytics** (`monetization_analytics.py`)
  - Boundary: `MonetizationAnalyst.evaluate(metrics, weights, intent_baseline)`
  - Contract: metrics dict -> `MonetizationInsight`
  - Limitation: uses aggregate heuristics; no cohort-segmented recommendation policy yet.

Implementation evidence: `tests/test_adaptive_loops.py`, `tests/test_priority3_expansion.py`.

### 3.3 Still deferred target-state capabilities

These remain roadmap items and should not be treated as current dependencies:

- Standalone ingestion pipeline service (polling/compaction/staleness/DLQ control plane).
- Standalone intelligence-engine serving runtime with confidence gating + failover orchestration.
- Asynchronous creative-orchestrator worker fabric and failed-prompt-family quarantine automation.
- Full experiment-and-post service infrastructure for queue rebalancing, auth-failure cancellation, and cohort routing at platform scale.
- End-to-end model snapshot registry and rollback automation for adaptive loops.

### 3.4 Explicit interface boundaries and contracts currently in use

- **Workflow-stage boundary (`src/main.py`)**
  - Contract is protocol-based and intentionally narrow:
    - `TrendSource.fetch_signals(topic) -> dict`
    - `CreativeEngine.generate_candidates(signals) -> list[dict]`
    - `PolicyGuard.validate(candidates) -> list[dict]`
    - `Publisher.publish(approved, dry_run) -> list[dict]`
    - `Analytics.collect(published) -> dict`
  - Each run emits structured log events with `trace_id`.

- **Domain orchestration boundary (`src/instagram_ai_system/orchestration.py`)**
  - `InstagramAISystem.run_creation_cycle(observed_reels)` returns `CycleOutput`.
  - `register_post_metrics(metrics)` feeds optimizer reward updates and persistence.
  - Persistence integration is behind `ExperimentStateRepository` to keep orchestration decoupled.

- **Integration boundaries (`src/integrations`)**
  - Publishing path uses explicit dataclasses (`PublishRequest`, `PublishResult`) with governance requirements.
  - Trend ingestion path uses `TrendSourceAdapter` protocol and canonical `NormalizedTrend` representation.

## Niche & Account Strategy Engine (Pre-Loop Layer)

A new pre-loop strategy layer now sits *before* the content loop and is responsible for selecting and continually updating the best account/niche concepts.

### Runtime placement

```text
Niche Candidate Generator
  -> Market & Demand Signals
  -> Competition/Saturation Analysis
  -> Feasibility & Compliance Checks
  -> Monetisation Path Scoring
  -> Success Probability Ranking
  -> Portfolio Selection (2-6 niches)
  -> Content Creation Loop
```

### Implemented service contract

`src/instagram_ai_system/niche_strategy_engine.py` exposes:

- `generate_candidates()`
- `collect_signals(candidates)`
- `score_candidates(candidates, signals)`
- `select_portfolio(top_k)`
- `evaluate_results(performance_snapshots)`
- `update_model()`
- `build_decision_report(ranked, portfolio)`

### Persistence and contracts

Storage models and migration introduce:

- `niche_candidates`
- `niche_scores`
- `account_experiments`
- `experiment_posts`
- `experiment_metrics`
- `model_versions`

Canonical schema contracts added in `schemas/`:

- `niche_candidate.schema.json`
- `niche_score_breakdown.schema.json`
- `experiment_plan.schema.json`
- `experiment_outcome.schema.json`

## 4) End-to-End Flow (Current Runtime)

```text
Local/External Trend Signals
  -> Candidate Generation
    -> Policy Validation
      -> Publish (or Dry-Run Simulation)
        -> KPI Collection
          -> Optimization State Update
```

This flow exists today across `src/main.py`, `src/instagram_ai_system/orchestration.py`, and `src/integrations/*` modules.

## 5) Contracts / Payload Envelope Migration

The system-level contract for generated and exchanged artifacts is the envelope shape:

```json
{
  "schema_version": "1.0",
  "trace_id": "...",
  "created_at": "...",
  "payload": { "...": "..." }
}
```

### Compatibility behavior (migration window)

- All producers should emit the envelope contract via the shared compatibility utility (`coerce_to_envelope`).
- Consumers can accept either:
  - fully enveloped payloads (preferred), or
  - legacy plain payload objects (temporary migration behavior).
- Legacy plain-payload acceptance is controlled by `INSTAGRAM_AI_ACCEPT_LEGACY_PAYLOADS`:
  - default: enabled (`1` / unset)
  - disable: set to `0`, `false`, `no`, or `off`

### Sunset timeline

- **Now through 2026-06-30**: dual-read mode (enveloped + legacy plain payloads).
- **Starting 2026-07-01**: strict mode in all environments (`INSTAGRAM_AI_ACCEPT_LEGACY_PAYLOADS=0`) and legacy payload inputs are rejected.
- **Post-sunset cleanup**: remove legacy-acceptance code path after one full release cycle in strict mode.
