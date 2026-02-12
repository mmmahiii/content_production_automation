# Content Production Automation Architecture

## 1) Purpose and Scope

This document defines the initial architecture for an end-to-end content production system that:

1. Ingests trend signals.
2. Generates content concepts.
3. Builds an asset package.
4. Queues publishable content.
5. Collects performance feedback.
6. Updates model prompts based on outcomes.

The goal is **independent module development** via explicit interface contracts.

---

## 2) Initial Repository Layout

```text
src/
  content_generation/
  trend_analysis/
  scoring/
  orchestration/
  storage/
  integrations/
    instagram/
docs/
  ARCHITECTURE.md
```

### Module Responsibilities

- `src/trend_analysis/`: Collect and normalize trend signals from multiple sources.
- `src/content_generation/`: Generate concepts and content briefs from trend signals.
- `src/scoring/`: Score concepts/assets for relevance, quality, and risk.
- `src/orchestration/`: Coordinate workflow transitions and retries.
- `src/storage/`: Persist canonical objects and audit history.
- `src/integrations/instagram/`: Platform-specific publishing and performance sync.

---

## 3) End-to-End Data Flow

```text
Trend Ingestion
  -> Concept Generation
    -> Asset Package
      -> Publish Queue
        -> Performance Feedback
          -> Model Prompt Update
```

### Step-by-Step

1. **Trend ingestion** (`trend_analysis`)
   - Pull signals from APIs/feeds (hashtags, topics, competitor activity).
   - Normalize into `TrendSignal[]`.
   - Persist raw + normalized records.

2. **Concept generation** (`content_generation`)
   - Consume high-confidence trend signals.
   - Produce `ContentConcept[]` with rationale and audience fit.

3. **Asset package assembly** (`content_generation` + `scoring`)
   - Build package candidates (caption, visual brief, CTA, hashtags).
   - Score packages for brand alignment, safety, and expected performance.
   - Output `AssetPackage` + `ScoreCard`.

4. **Publish queue** (`orchestration` + `integrations/instagram`)
   - Validate scheduling constraints and channel rules.
   - Enqueue `PublishJob`.
   - Execute publish action and track status transitions.

5. **Performance feedback** (`integrations/instagram` + `trend_analysis`)
   - Fetch post-performance metrics (reach, saves, watch time, CTR).
   - Link metrics to originating concept and package.
   - Produce `PerformanceFeedback`.

6. **Model prompt update** (`scoring` + `content_generation`)
   - Aggregate outcomes and detect winning patterns.
   - Generate prompt deltas and versioned `PromptProfile` updates.
   - Store prompt changes with explainability metadata.

---

## 4) System Boundaries and Interaction Style

- Modules communicate through **typed contracts** (JSON-serializable payloads).
- Recommended interaction patterns:
  - Sync for deterministic transforms (e.g., scoring a single package).
  - Async/event-driven for workflow steps (e.g., publish + feedback).
- Every contract includes:
  - `schema_version`
  - `trace_id`
  - `created_at`

---

## 5) Interface Contracts (I/O Schemas)

> These are canonical v1 schemas to unblock parallel implementation. Teams can generate language-specific types from these structures.

### 5.1 Shared Envelope

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "2026-01-01T00:00:00Z",
  "payload": {}
}
```

### 5.2 Trend Analysis Contracts

#### Input: `TrendIngestionRequest`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "sources": ["instagram", "google_trends", "social_listening"],
    "time_window_hours": 24,
    "geo": "US",
    "language": "en"
  }
}
```

#### Output: `TrendSignalBatch`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "signals": [
      {
        "trend_id": "string",
        "topic": "quiet luxury",
        "platform": "instagram",
        "velocity": 0.87,
        "confidence": 0.91,
        "audience_segments": ["gen_z", "fashion_interest"],
        "evidence": {
          "sample_size": 1200,
          "examples": ["#quietluxury", "#capsulewardrobe"]
        }
      }
    ]
  }
}
```

### 5.3 Content Generation Contracts

#### Input: `ConceptGenerationRequest`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "trend_signals": ["TrendSignal"],
    "brand_guidelines_ref": "bg_v3",
    "campaign_context": {
      "objective": "engagement",
      "target_audience": ["gen_z"],
      "constraints": ["no comparative claims"]
    },
    "prompt_profile_id": "prompt_profile_v12"
  }
}
```

#### Output: `ContentConceptBatch`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "concepts": [
      {
        "concept_id": "string",
        "title": "3 Outfit Formula for Quiet Luxury",
        "hook": "You only need 3 pieces to look expensive.",
        "format": "reel",
        "rationale": "High overlap with current trend + evergreen utility",
        "expected_audience_fit": 0.84,
        "source_trend_ids": ["trend_001", "trend_017"]
      }
    ]
  }
}
```

### 5.4 Scoring Contracts

#### Input: `AssetScoringRequest`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "concept_id": "string",
    "asset_package": {
      "caption": "string",
      "visual_brief": "string",
      "hashtags": ["string"],
      "cta": "string"
    },
    "score_weights": {
      "brand_alignment": 0.3,
      "predicted_engagement": 0.4,
      "safety": 0.3
    }
  }
}
```

#### Output: `ScoreCard`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "concept_id": "string",
    "scores": {
      "brand_alignment": 0.92,
      "predicted_engagement": 0.76,
      "safety": 0.98,
      "composite": 0.86
    },
    "decision": "approve",
    "reasons": ["Strong brand tone match", "Low policy risk"]
  }
}
```

### 5.5 Orchestration + Publish Queue Contracts

#### Input: `PublishQueueRequest`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "concept_id": "string",
    "asset_package_id": "string",
    "channel": "instagram",
    "schedule_at": "2026-01-02T16:00:00Z",
    "priority": "normal"
  }
}
```

#### Output: `PublishJob`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "publish_job_id": "string",
    "status": "queued",
    "channel": "instagram",
    "attempt": 0,
    "next_retry_at": null
  }
}
```

### 5.6 Instagram Integration Contracts

#### Input: `InstagramPublishRequest`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "publish_job_id": "string",
    "media_type": "reel",
    "media_uri": "s3://bucket/key.mp4",
    "caption": "string",
    "hashtags": ["string"]
  }
}
```

#### Output: `InstagramPublishResult`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "publish_job_id": "string",
    "platform_post_id": "1789...",
    "status": "published",
    "published_at": "timestamp"
  }
}
```

### 5.7 Performance Feedback Contracts

#### Input: `PerformanceSyncRequest`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "platform_post_id": "1789...",
    "lookback_hours": 72
  }
}
```

#### Output: `PerformanceFeedback`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "platform_post_id": "1789...",
    "concept_id": "string",
    "metrics": {
      "impressions": 120000,
      "reach": 83000,
      "engagement_rate": 0.064,
      "saves": 2100,
      "shares": 900,
      "watch_through_rate": 0.41,
      "profile_click_rate": 0.017
    },
    "benchmark_delta": {
      "engagement_rate": 0.012,
      "watch_through_rate": -0.03
    }
  }
}
```

### 5.8 Prompt Update Contracts

#### Input: `PromptUpdateRequest`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "prompt_profile_id": "prompt_profile_v12",
    "feedback_batch": ["PerformanceFeedback"],
    "analysis_window_days": 14
  }
}
```

#### Output: `PromptProfileUpdate`

```json
{
  "schema_version": "1.0",
  "trace_id": "uuid",
  "created_at": "timestamp",
  "payload": {
    "prompt_profile_id": "prompt_profile_v13",
    "previous_profile_id": "prompt_profile_v12",
    "changes": [
      {
        "type": "instruction_addition",
        "path": "style.hook_patterns",
        "value": "Prefer utility-first opening lines in first 1.5 seconds"
      }
    ],
    "justification": "Utility-first hooks increased watch-through by +8%",
    "approval_required": true
  }
}
```

---

## 6) Storage Model (Logical)

`src/storage/` should expose repositories or gateways for:

- `trend_signals`
- `content_concepts`
- `asset_packages`
- `score_cards`
- `publish_jobs`
- `platform_posts`
- `performance_feedback`
- `prompt_profiles`
- `prompt_profile_history`

Each record must support:
- idempotent upsert (by natural keys where possible)
- immutable audit trail for state changes
- traceability (`trace_id`, upstream IDs)

---

## 7) Orchestration State Machine (Reference)

`orchestration` maintains these states per publish flow:

1. `trend_received`
2. `concept_generated`
3. `asset_scored`
4. `queued_for_publish`
5. `published`
6. `feedback_collected`
7. `prompt_updated`

Failure states:
- `failed_validation`
- `failed_publish_retryable`
- `failed_publish_terminal`

Retry policy (default):
- max attempts: `3`
- backoff: exponential (`2m`, `10m`, `30m`)

---

## 8) Non-Functional Requirements (Initial)

- **Observability**: structured logs + trace propagation across all modules.
- **Determinism**: scoring should be reproducible for same inputs/version.
- **Versioning**: contract and prompt profile versions are explicit.
- **Safety**: content must pass policy/safety gates before queueing.
- **Extensibility**: new channels should mirror `integrations/instagram` contract style.

---

## 9) Implementation Notes for Independent Teams

To work independently, each module team should:

- Implement contract validation at module boundaries.
- Produce consumer-driven contract tests.
- Return machine-readable errors with stable codes, e.g.:

```json
{
  "error": {
    "code": "INVALID_SCHEMA",
    "message": "Missing required field: payload.concept_id",
    "retryable": false
  }
}
```

Recommended milestone order:
1. Shared schemas + fixtures.
2. Trend ingestion MVP.
3. Concept generation + scoring.
4. Publish queue + Instagram adapter.
5. Feedback loop + prompt updater.

