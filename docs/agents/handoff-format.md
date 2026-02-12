# Agent Handoff Artifact Format

All inter-agent handoffs must use structured JSON payloads with a shared envelope.

## Envelope

```json
{
  "handoff_id": "uuid",
  "source_agent": "creative_director",
  "target_agent": "script_generator",
  "created_at": "2026-01-01T00:00:00Z",
  "model_version": "v1.0.0",
  "confidence": 0.82,
  "trace": {
    "strategy_cycle_id": "uuid",
    "upstream_refs": ["id1", "id2"]
  },
  "payload": {}
}
```

## Required Rules

- JSON schema validation is mandatory before acceptance.
- Confidence below threshold must include `needs_review: true` in payload.
- No free-form-only handoffs are allowed in production workflows.
- Every payload must include content-safety and policy tags.

## Core Payload Shapes

- Creative brief payload: mode, aesthetic, emotional angle, variant budget.
- Script payload: hooks array, narrative beats, overlays timeline, caption variants.
- Variant result payload: asset URIs, technical metadata, QA status.
- Learning update payload: metric deltas, policy recommendation, rollback token.
