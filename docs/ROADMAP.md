# Product & Delivery Roadmap

Phased roadmap from MVP to growth optimization and monetization. Each phase includes scope, deliverables, and exit criteria.

## Phase 1 — MVP (Weeks 1-4)

### Goal
Create a reliable end-to-end loop that can generate, schedule, publish, and evaluate content for one niche.

### Scope

- Single account support.
- One primary content format (short reels).
- Daily automated planning.
- Dry-run + approval gate before production publishing.

### Deliverables

1. Orchestrator entrypoint with deterministic step sequence.
2. Trend ingestion adapter with at least two data sources.
3. Prompt-driven creative generation with 3+ variants/post.
4. Publisher adapter with retry and idempotency keys.
5. Metrics ingestion pipeline and daily KPI report.

### Exit criteria

- 7 consecutive days of successful scheduled publishing.
- At least 20 posts generated/published with full audit metadata.
- Failures are observable and replayable from CLI operations.

## Phase 2 — Optimization (Weeks 5-8)

### Goal
Increase engagement efficiency and reduce manual intervention.

### Scope

- Multi-variant testing for hooks/captions.
- Automated strategy updates from KPI feedback.
- Quality/policy scoring before publish.

### Deliverables

1. A/B test engine for first 3 seconds hook hypotheses.
2. Strategy service that updates template weights weekly.
3. Auto-pruning of underperforming formats/topics.
4. Cost/performance dashboard (token + rendering + reach).

### Exit criteria

- +25% median engagement uplift vs MVP baseline.
- 50% reduction in human approvals needed per week.
- Stable policy compliance with <1% flagged content.

## Phase 3 — Monetization (Weeks 9-12)

### Goal
Translate audience growth into measurable revenue streams.

### Scope

- CTA optimization and funnel instrumentation.
- Lead magnet / affiliate / offer experimentation.
- Revenue attribution linked to content variants.

### Deliverables

1. Monetization experiment framework (offer x format x audience).
2. Link tracking and attribution integration.
3. Revenue KPI dashboard (RPM, conversion rate, CAC proxy).
4. Automatic budget allocation to highest-performing strategy segments.

### Exit criteria

- First recurring revenue events attributable to system content.
- Positive trend in weekly revenue per 1k views.
- Written operating model for scaling to additional accounts.

## Cross-phase engineering enablers

Implement these continuously across all phases:

- Test coverage for orchestrator and adapters.
- Structured logging + tracing.
- Feature flags for rollout safety.
- Prompt/version registry with rollback support.
- Data retention and deletion policies for compliance.

## Milestone table

| Milestone | Target week | Success metric |
|---|---:|---|
| M1: loop skeleton live | 2 | dry-run executes end-to-end |
| M2: production posting | 4 | 98% publish success rate |
| M3: adaptive strategy | 7 | weekly template weight updates |
| M4: optimization stable | 8 | +25% engagement vs baseline |
| M5: monetization pilots | 10 | first attributable conversions |
| M6: monetization repeatable | 12 | weekly recurring revenue |
