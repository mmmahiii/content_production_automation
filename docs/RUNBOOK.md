# Operations Runbook

Runbook for operating the daily automation loop. Use this once the first production-like pipeline is deployed.

## Operational objectives

- Maintain reliable daily publishing cadence.
- Detect regressions in reach/engagement quickly.
- Continuously improve content strategy using measured signals.

## SLOs and guardrails

## Publish governance controls (must-read)

The publish stage in `production_loop.py` is simulation-first by design.

- Default mode is simulation (`ALLOW_AUTONOMOUS_PUBLISH=false`).
- Live publish requires **all three** env vars set to truthy values:
  - `ALLOW_AUTONOMOUS_PUBLISH`
  - `PUBLISH_APPROVAL_GRANTED`
  - `GOVERNANCE_APPROVED`
- Missing any signal forces a simulated publish payload and logs the reason.

Recommended operational practice:
1. Keep `ALLOW_AUTONOMOUS_PUBLISH=false` in baseline environments.
2. Enable all three values only in approved release windows.
3. Reset approvals to false after window closes.


- **Publishing success rate (24h):** `>= 98%`
- **Failed-job mean time to recovery:** `< 30 minutes`
- **Time-to-detect severe performance drop:** `< 24 hours`
- **Max daily post volume variance:** `<= +/- 1 post` from plan

## Daily operations checklist

Perform at the start of each day (or shift):

1. Check orchestration dashboard for failed jobs in last 24h.
2. Confirm next 24h post queue is populated and approved.
3. Verify rate-limit headroom for Instagram APIs.
4. Review previous day KPI summary:
   - reach
   - watch time / retention
   - saves
   - shares
   - profile clicks
5. Validate anomalies and trigger remediation if thresholds crossed.

## Daily command set (example)

```bash
# Inspect worker/scheduler health
uv run python -m src.main --ops health-check

# Enqueue one production run (daily scheduler target)
uv run python -m src.main --ops enqueue-daily --topic "ai productivity"

# Process one queued run end-to-end (worker target)
uv run python -m src.main --ops run-worker --topic "ai productivity"

# Retry failed publishing tasks
uv run python -m src.main --ops replay-failed --since-hours 24

# Generate KPI snapshot report
uv run python -m src.main --ops kpi-report --period daily
```

## Weekly operations checklist

Perform once per week:

1. Compare 7-day vs prior 7-day performance by content format.
2. Retire bottom 20% performing prompt templates.
3. Promote top 20% templates into default strategy set.
4. Refresh trend sources and niche hypothesis backlog.
5. Audit policy violations and false-positive moderation flags.
6. Review infra cost (tokens, rendering, storage) and optimize.

## Weekly command set (example)

```bash
uv run python -m src.main --ops kpi-report --period weekly
uv run python -m src.main --ops template-rank --period 30d
uv run python -m src.main --ops strategy-refresh
uv run python -m src.main --ops cost-report --period weekly
```

## Incident response playbooks

### A) Publishing failure spike (>5% in 1h)

1. Pause auto-publish in orchestrator.
2. Inspect latest API errors (auth/rate limit/media validation).
3. Re-run one failed payload in sandbox mode.
4. Apply fix (token refresh, backoff increase, media re-encode).
5. Replay backlog gradually and monitor error rate.

### B) Engagement collapse (>30% down day-over-day)

1. Confirm no tracking outage in analytics collectors.
2. Segment drop by format/topic/time-slot.
3. Roll back to last known good prompt strategy.
4. Trigger 24h high-velocity A/B tests on hooks and opening frames.
5. Present postmortem and strategy adjustment in weekly review.

### C) Policy/compliance event

1. Immediately halt scheduled publishing.
2. Identify and quarantine violating assets.
3. Patch moderation rules and prompt constraints.
4. Require human approval for next 48h.
5. Document incident and permanent prevention action.

## Escalation matrix (starter)

- **L1 (on-call engineer):** triage, restart/retry, basic rollback.
- **L2 (automation owner):** orchestration fixes, model/template changes.
- **L3 (product/compliance lead):** policy decisions, external comms.

## Logging and audit requirements

- Every generated asset must have: prompt version, model ID, source signals, timestamp.
- Every publish attempt must log: payload hash, target account, response code, retry count.
- Every optimization decision must log: KPI evidence and strategy delta.

## End-of-day signoff

Before ending shift:

- 24h queue populated.
- unresolved incidents documented with owner + ETA.
- KPI and anomaly summary posted to team channel.
