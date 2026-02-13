# Adaptive Content Organism: System Design

This document now distinguishes between the **current implementation** and the **target-state architecture** so engineers can avoid building against stale assumptions.

## Current State vs Target State

### 1) Current implemented modules and responsibilities

Current implementation is package-oriented and centered on three roots:

- `src/main.py`
  - Runtime orchestrator entrypoint for cycle execution and ops commands.
  - Defines protocol contracts for trend source, generation, policy guard, publishing, and analytics.

- `src/instagram_ai_system`
  - Strategy/config models, trend intelligence, creativity/content generation, script and idea generation, schema validation, scheduling metadata, experiment optimization, performance ingestion, and orchestration.
  - Includes `storage/` subpackage for DB setup and repositories.

- `src/integrations`
  - `instagram/`: publisher and metrics integration utilities.
  - `trends/`: adapter protocol and normalized external trend ingestion.

### 2) Deferred modules from system design

The following target-state services are **deferred** (not implemented as standalone modules yet):

- `mode-controller`
- shadow-testing subsystem within `experiment-and-post`
- `monetization-analyst`
- `learning-loop`

### 3) Explicit interface boundaries and contracts currently in use

Current interface contracts are:

- `src/main.py` protocol boundaries:
  - `fetch_signals -> generate_candidates -> validate -> publish -> collect`
  - JSON-style dict/list payload handoffs with per-cycle `trace_id` logging.
- `src/instagram_ai_system/orchestration.py` boundaries:
  - creation cycle output via `CycleOutput`
  - feedback contract via `register_post_metrics(...)` and optimizer state persistence.
- `src/integrations/instagram/publisher.py` boundaries:
  - explicit `PublishRequest` and `PublishResult`
  - governance approvals, idempotency key semantics, retries, and audit events.
- `src/integrations/trends/adapters.py` boundaries:
  - `TrendSourceAdapter` protocol
  - canonical normalized `NormalizedTrend` records.

## Target Service Map by Layer

| Layer | Target Service / Module | Inputs | Outputs | Trigger Cadence | Failure Handling | Downstream Dependencies |
|---|---|---|---|---|---|---|
| 1. Data Ingestion | `ingestion-pipeline` | Reels metadata scrapes, IG Graph API responses, audio trend feed, comments | Normalized virality events | Near-real-time (5-15 min polling), hourly compaction | Retry with exponential backoff; mark source stale after 3 failures; dead-letter queue | Feature store, pattern discovery |
| 2. Virality Intelligence | `intelligence-engine` | Virality events, historical feature store, creator profile priors | Pattern reports, score models, idea scoring decisions | Hourly incremental, daily full refresh | Fall back to last healthy model; confidence floor gating | Creative Director, mode controller |
| 3. Creative Generation | `creative-orchestrator` + generation workers | Strategy briefs, score bands, mode constraints, disallowed themes | Variant packages (hook/caption/overlay/video variants) | Event-driven when an idea is approved | If generation job fails, regenerate variant with alternate template; quarantine failed prompt families | Shadow testing, posting engine |
| 4. Testing & Posting | `experiment-and-post` | Variant packages, schedule windows, hashtag/caption policies | Shadow test metrics, promoted post jobs, publishing logs | Shadow launch every approved batch; publish per schedule policy | Cancel jobs on auth or platform errors; retry with jitter; post queue rebalancing | Feedback loop, audit log |
| 5. Feedback Learning | `learning-loop` *(deferred)* | Real-time performance metrics, predicted scores, experiment outcomes | Model deltas, exploration coefficient updates, strategy constraints | 15-min incremental, 48-hour policy updates | Freeze adaptive updates on anomaly; roll back to prior model snapshot | Mode controller, intelligence engine |
| 6. Monetization Intelligence | `monetization-analyst` *(deferred)* | Audience composition, intent comments, saves/follows, profile actions | Monetization opportunity scores, segment drift alerts, strategy nudges | Daily + weekly strategic review | Hold recommendations when confidence low; request more exploration in affected segment | Creative Director, objective optimizer |

## One Full Target Cycle Sequence (Text Diagram)

1. `ingestion-pipeline` pulls latest reels, comments, and audio trend signals.
2. Pipeline emits normalized `virality_event` records and writes to the feature store.
3. `intelligence-engine` updates pattern clusters and computes score for candidate ideas.
4. `mode-controller` *(deferred)* picks mode (Exploit / Explore / Mutation / Chaos) based on risk and recency performance.
5. `creative-orchestrator` requests structured variants from specialized generators.
6. `experiment-and-post` sends variants to shadow testing accounts/cohorts.
7. After the observation window, experiment service selects winner and promotes to primary distribution.
8. Live performance metrics flow into `learning-loop` *(deferred)* for predicted-vs-actual error analysis.
9. `learning-loop` *(deferred)* updates model priors and exploration coefficient.
10. `monetization-analyst` *(deferred)* updates conversion-intent and audience-quality guidance for next cycle.

## Operational Non-Functional Requirements

- **Observability:** every stage emits latency, error, and confidence metrics.
- **Idempotency:** ingestion and publishing jobs use deterministic keys to prevent duplicates.
- **Auditability:** all strategy decisions and model version references are persisted.
- **Safety:** disallowlist filters apply before generation and before posting.

## Adaptive Loop Feature Flags and Rollout Gates

To safely introduce post-analytics adaptation loops, keep each loop behind an independent gate that can be enabled per environment.

### Feature flags

- `enable_experiment_lifecycle`
  - Enables variant lifecycle automation (winner promotion + archive marker writes).
  - Keep disabled until experiment arm-state persistence is verified in staging.
- `enable_learning_loop`
  - Enables observed-vs-predicted error updates that tune exploration pressure (`epsilon_exploration`).
  - Keep disabled during baseline measurement windows to avoid moving-target evaluations.
- `enable_objective_strategy`
  - Enables objective-aware strategy updates that rebalance KPI reward weights from KPI deltas.
  - Roll out only after KPI delta data quality checks pass.

### Rollout gates

1. **Shadow gate:** Run loop calculations and logs only (no state mutation) for at least 7 days.
2. **Canary gate:** Enable each loop for a limited objective segment (for example 10% of campaigns).
3. **Stability gate:** Require no anomaly alerts and bounded parameter changes for 3 consecutive days.
4. **Scale gate:** Expand to full traffic, keeping a hard disable switch for immediate rollback.

### Operational guardrails

- Keep lifecycle winner promotion behind minimum sample thresholds.
- Bound learning-loop exploration changes with floor/ceiling limits.
- Normalize objective weight updates after each adjustment to preserve a stable reward function.
- Emit traceable update payloads in cycle summaries for observability and auditability.


## Niche & Account Strategy Engine (Pre-Loop Layer)

The strategy engine is integrated as an upstream layer before content generation. It handles candidate generation, signal collection, score-based ranking, portfolio selection, and experiment-driven model updates.

- Service module: `src/instagram_ai_system/niche_strategy_engine.py`
- Persistence tables: `niche_candidates`, `niche_scores`, `account_experiments`, `experiment_posts`, `experiment_metrics`, `model_versions`
- Contracts: `schemas/niche_candidate.schema.json`, `schemas/niche_score_breakdown.schema.json`, `schemas/experiment_plan.schema.json`, `schemas/experiment_outcome.schema.json`
