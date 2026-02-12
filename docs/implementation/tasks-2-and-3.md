# Implementation Tasks for Next Priorities (#2 and #3)

This task list breaks down the next two priorities:

- **#2:** Unified contract envelope (`schema_version`, `trace_id`, `created_at`) across core payloads.
- **#3:** Runbook operations hardening (persisted replay + richer KPI reporting).

---

## Priority #2 — Unified Contract Envelope

### Goal
Ensure all core generated/ingested payloads share a standard envelope:

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "ISO-8601",
  "payload": {}
}
```

### Task 2.1 — Define envelope contract and helper
- Add a reusable envelope builder in `src/instagram_ai_system`.
- Add validation helper(s) to enforce required envelope fields.
- Decide compatibility strategy for existing unwrapped payloads (feature flag or migration mode).

**Acceptance criteria**
- Common helper used by all new envelope-enabled services.
- Unit tests cover valid/invalid envelope creation.

### Task 2.2 — Wrap PRD feature outputs
- Update these services to emit wrapped payloads:
  - `idea_generation.py`
  - `script_generation.py`
  - `scheduling_metadata.py`
  - `performance_ingestion.py` summaries where applicable
- Keep inner payload shape unchanged to limit migration risk.

**Acceptance criteria**
- Existing semantic payload content remains intact under `payload` key.
- All updated services include `schema_version`, `trace_id`, `created_at`.

### Task 2.3 — Update JSON schemas and schema validation
- Add envelope-aware schemas (or compose envelope + inner schema).
- Update `schema_validation.py` tests and schema contract tests.
- Ensure date-time parsing/format expectations are explicit.

**Acceptance criteria**
- Contract tests pass for both positive and negative envelope cases.
- Validation errors clearly identify envelope field violations.

### Task 2.4 — Migration and adapter compatibility
- Add adapter/unwrap utility for existing callers that expect old top-level keys.
- Update tests and any direct field access in orchestration/integration tests.
- Document migration notes in `docs/ARCHITECTURE.md` or setup notes.

**Acceptance criteria**
- No runtime breakage in current orchestrator/test flow.
- Backward compatibility documented with sunset plan.

---

## Priority #3 — Runbook Operations Hardening

### Goal
Make runbook operations stateful, replayable, and operationally useful in line with `docs/RUNBOOK.md`.

### Task 3.1 — Persist operation runs and outcomes
- Add storage model/repository for ops run records:
  - operation name
  - request parameters
  - status/result payload
  - trace id, timestamps
- Wire `_run_ops` in `src/main.py` to persist every operation run.

**Acceptance criteria**
- Each ops invocation creates an auditable persisted record.
- Failed ops record error details and status.

### Task 3.2 — Replay failed jobs from persisted state
- Implement a concrete `replay-failed` path that replays persisted failed publish attempts/jobs.
- Add deterministic idempotency behavior for replayed items.
- Emit structured replay summary (requested, replayed, skipped, still_failed).

**Acceptance criteria**
- Replays are idempotent and auditable.
- Replay command returns actionable counts.

### Task 3.3 — KPI report enrichment
- Expand `kpi-report` output to include:
  - per-post metrics (where available)
  - period aggregates
  - objective-aligned metrics (reach/saves/shares/watch-through)
  - anomaly flags
- Add filtering options (`--period`, optional topic/window filters).

**Acceptance criteria**
- Daily and weekly reports include structured KPI sections.
- Output supports both human-readable summary and machine parsing.

### Task 3.4 — Health-check hardening
- Expand `health-check` to verify database connectivity and repository readiness.
- Include dependency status map in response payload.
- Return non-OK status when critical dependencies are unavailable.

**Acceptance criteria**
- Health check differentiates degraded vs healthy states.
- Tests cover healthy/degraded outcomes.

### Task 3.5 — Test coverage for ops workflows
- Add integration-style tests for all ops commands and failure modes.
- Cover replay idempotency and persistence correctness.
- Keep deterministic fixtures for repeatability.

**Acceptance criteria**
- Ops test suite validates expected runbook command behaviors.
- New tests pass in CI/local default run.

---

## Suggested execution order
1. Task 2.1
2. Task 2.3
3. Task 2.2
4. Task 2.4
5. Task 3.1
6. Task 3.2
7. Task 3.3
8. Task 3.4
9. Task 3.5

This order minimizes breakage by establishing envelope primitives and validation before migrating producers, then hardening operational persistence before replay/reporting features.
