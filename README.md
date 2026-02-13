# Content Production Automation

Implementation-first blueprint for an AI-driven automation system that discovers viral trends, generates creative Instagram content, publishes on schedule, and continuously optimizes performance for monetization.

## What this repository is for

This repo defines the operating model and starter contract for an autonomous content loop:

1. **Ingest** trend and account signals from Instagram + external sources.
2. **Generate** multiple creative assets (hooks, scripts, captions, visuals).
3. **Review** safety, policy, and quality requirements.
4. **Publish** to Instagram with resilient scheduling and retry behavior.
5. **Analyze** outcomes and feed results into planning.
6. **Optimize** toward growth + monetization KPIs.

The goal is to make it easy for an engineer to start building the system immediately with minimal ambiguity.

## Current code layout (source of truth)

> ⚠️ Older docs in this repo reference an initial “`content_generation/`, `trend_analysis/`, `scoring/`” tree. That layout is **not** the current implementation and should not be used for new development.

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

## Current State vs Target State

### 1) Current implemented modules and responsibilities

- `src/main.py`: runnable orchestrator entrypoint with protocol-based interfaces (`TrendSource`, `CreativeEngine`, `PolicyGuard`, `Publisher`, `Analytics`) and local adapters for dry-run/local modes.
- `src/instagram_ai_system/`: domain package for trend intelligence, creative generation, scheduling metadata, experiment optimization, performance ingestion, and system orchestration.
- `src/instagram_ai_system/storage/`: persistence layer abstractions and SQLAlchemy-backed database/repository modules for experiment state and related entities.
- `src/integrations/instagram/`: publishing integration (governance gate, idempotency, retry/audit behavior) plus metrics normalization/aggregation helpers.
- `src/integrations/trends/`: external trend adapter contracts and normalization for multi-source trend ingestion.
- `src/instagram_ai_system/production_loop.py`: production vertical slice runner with real trend ingestion (Reddit), script+asset planning, render, publish/simulate, metrics pull, checkpointing, and learning snapshots.

### 2) Deferred modules from system design

The following modules appear in system design documentation but are not yet implemented as first-class runtime modules:

- **mode controller** (dynamic exploit/explore/mutation/chaos policy service)
- **shadow testing** (traffic splitting + winner promotion loop)
- **monetization analyst** (segment/conversion-intent guidance engine)
- **learning loop** (automated model-delta updates from predicted-vs-actual errors)

### 3) Explicit interface boundaries and contracts currently in use

Current boundaries are protocol and dataclass driven:

- **Entrypoint orchestration contract** in `src/main.py`:
  - Inputs/outputs between workflow stages are Python dict/list payloads.
  - Stage order contract: fetch signals → generate candidates → validate candidates → publish → collect analytics.
  - Structured JSON event logging carries `trace_id` across steps.
- **Domain orchestration contract** in `src/instagram_ai_system/orchestration.py`:
  - `InstagramAISystem` composes trend engine, creativity engine, factory, optimizer, and optional experiment-state repository.
  - `run_creation_cycle(...)` returns `CycleOutput` with selected briefs and top patterns.
  - `register_post_metrics(...)` updates optimizer state and optionally persists arm stats.
- **Integration contracts**:
  - `src/integrations/instagram/publisher.py` defines `PublishRequest`/`PublishResult`, required approvals, idempotency semantics, retry policy, and audit trail.
  - `src/integrations/trends/adapters.py` defines `TrendSourceAdapter` plus canonical `NormalizedTrend` records.

## Documentation map

- [Setup guide](docs/SETUP.md): Required environment variables, local boot commands, and secrets handling conventions.
- [Operations runbook](docs/RUNBOOK.md): Daily/weekly production procedures and incident flows.
- [Delivery roadmap](docs/ROADMAP.md): Milestones from MVP to optimization and monetization.
- [Architecture](docs/ARCHITECTURE.md): Current architecture and implementation-aligned module map.
- [System design](docs/architecture/system-design.md): Target-state layered design and deferred capabilities.

## Suggested first build order

1. Extend `src/main.py` adapters from local stubs to production connectors.
2. Deepen `src/instagram_ai_system/storage` persistence for content plans, assets, and posting logs.
3. Expand trend ingestion and planner loops via `src/integrations/trends` + `trend_intelligence`.
4. Integrate generation with manual approval workflows.
5. Wire Instagram publishing and metrics sync end-to-end.
6. Add adaptive optimization and deferred target-state services incrementally.

## Definition of done (MVP)

MVP is complete when the system can:

- Generate a 7-day content calendar automatically.
- Produce at least 3 post variants/day from trend + performance inputs.
- Publish at scheduled times with retry support.
- Persist engagement metrics and produce a weekly optimization report.

See [docs/ROADMAP.md](docs/ROADMAP.md) for detailed milestones and acceptance criteria.
