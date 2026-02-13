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
  - `storage/`: database session management plus repositories/models for persisted experiment state.

- **Integration package (`src/integrations`)**
  - `instagram/publisher.py`: publish request/result contract, governance approval gate, idempotency, retries, audit entries.
  - `instagram/metrics.py`: Instagram metrics normalization and rollup helpers.
  - `trends/adapters.py`: multi-source trend adapter protocol and normalized trend model.

### 3.2 Deferred modules from system design

The system-design target includes modules that are not yet implemented as dedicated runtime components:

- **Mode controller** (dynamic mode policy service)
- **Shadow testing** (controlled variant rollout + winner promotion)
- **Monetization analyst** (audience quality and conversion-intent guidance)
- **Learning loop** (continuous model/prior updates from prediction error)

These remain planned capabilities and should be treated as roadmap items, not current dependencies.

### 3.3 Explicit interface boundaries and contracts currently in use

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
