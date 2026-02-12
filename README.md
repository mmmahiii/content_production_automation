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

## Documentation map

- [Setup guide](docs/SETUP.md): Required environment variables, local boot commands, and secrets handling conventions.
- [Operations runbook](docs/RUNBOOK.md): Daily/weekly production procedures and incident flows.
- [Delivery roadmap](docs/ROADMAP.md): Milestones from MVP to optimization and monetization.
- [Entrypoint contract](src/main.py): Minimal orchestration sequence and interface contract.

## Recommended local architecture

Use a modular service layout to reduce coupling and simplify iterative delivery:

- **orchestrator**: owns workflow state machine and job scheduling.
- **trend-intel**: pulls reels/accounts data and computes content opportunities.
- **creative-engine**: produces scripts, captions, visual prompts, and variants.
- **render-pipeline**: transforms generated assets into publish-ready media.
- **publisher**: posts content and handles retries/backoff.
- **analytics**: computes KPI deltas and writes feedback signals.
- **policy-guard**: validates brand, legal, and platform policy constraints.

For MVP, these can be modules in one codebase; split into services only when scaling demands it.

## Suggested first build order

1. Implement `src/main.py` orchestration interfaces with mocked adapters.
2. Add storage (SQLite/Postgres) for content plans, assets, and posting logs.
3. Build trend ingestion + planner loop for one niche/topic.
4. Integrate generation and manual approval.
5. Add publishing and analytics sync.
6. Automate optimization decisions based on KPI thresholds.

## Definition of done (MVP)

MVP is complete when the system can:

- Generate a 7-day content calendar automatically.
- Produce at least 3 post variants/day from trend + performance inputs.
- Publish at scheduled times with retry support.
- Persist engagement metrics and produce a weekly optimization report.

See [docs/ROADMAP.md](docs/ROADMAP.md) for detailed milestones and acceptance criteria.
