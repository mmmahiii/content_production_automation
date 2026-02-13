# Product Requirements Document (PRD): Instagram Content Production Automation MVP

## 1) Product Scope and Target

### 1.1 Product vision source
This PRD translates the current repository vision—"a full AI system" to run and optimize a monetizable Instagram page with continuously improving Reel curation—into a bounded, testable MVP scope.

### 1.2 Target account niches (MVP)
The MVP supports **three launch niches** with similar short-form behavior patterns and broad monetization potential:
1. **Personal productivity and self-improvement**
2. **Fitness and body recomposition**
3. **Personal finance basics**

Rationale for MVP: these niches have high Reel consumption, strong hook dependence, and measurable engagement loops suitable for iterative optimization.

### 1.3 Target audience
- **Primary age band:** 18–34
- **Platform behavior:** mobile-first, short attention span, likely to consume Reels in feed and Explore
- **User intent:** discover practical ideas quickly; save/share concise, actionable content

### 1.4 Supported content formats
The system must generate and manage assets for:
- **Reels concepts** (topic + angle + audience intent)
- **Hooks** (opening 1–2 lines to maximize retention)
- **Captions** (short + long variants with CTA)
- **Thumbnail text concepts** (3–7 word overlay options)

---

## 2) MVP Features (Only)

The MVP includes exactly these features:

1. **Idea generation**
2. **Script generation**
3. **Scheduling metadata generation**
4. **Performance ingestion**

Any functionality outside these four is out of scope unless explicitly listed in section 5 acceptance criteria as required support behavior.

---

## 3) Functional Requirements and Acceptance Criteria

## 3.1 Feature A: Idea Generation

### Description
Generate ranked Instagram Reel ideas per niche, including angle, intended audience reaction, and reusable hook options.

### Inputs
- Niche (one of the 3 MVP niches)
- Optional sub-topic keywords
- Optional tone preference (e.g., educational, contrarian, motivational)

### Outputs
For each generated idea:
- Idea title
- One-sentence premise
- Audience pain point or desire
- At least 3 hook options
- Suggested thumbnail text (at least 2 options)
- Suggested caption direction (1 short brief)

### Acceptance criteria
1. Given a valid niche, the system returns **at least 10 unique ideas** in one generation request.
2. Every idea includes all required output fields listed above.
3. Hooks are non-empty and distinct within the same idea (minimum string distance check or dedup logic).
4. Output is machine-readable (JSON schema or equivalent structured format).
5. Generation request completes in **<= 15 seconds** for 10 ideas under nominal local runtime.

## 3.2 Feature B: Script Generation

### Description
Turn a selected idea into a production-ready Reel script optimized for short-form retention.

### Inputs
- Selected idea object from Feature A
- Desired duration bucket: 15s, 30s, or 45s
- Tone and CTA preference

### Outputs
- Script with timestamped segments (Hook, Body beats, CTA)
- On-screen text suggestions per segment
- Caption draft (short and long variant)
- Hashtag suggestions (5–10)

### Acceptance criteria
1. Script output includes all sections: Hook, Body, CTA.
2. Total script duration estimate is within **+/- 20%** of selected duration bucket.
3. Caption output includes **2 variants** (short and long).
4. Hashtag list length is between 5 and 10, no duplicates.
5. Structured output persists a reference to source idea ID.

## 3.3 Feature C: Scheduling Metadata Generation

### Description
Generate publish-ready metadata package for downstream scheduling tools (without posting autonomously).

### Inputs
- Script package from Feature B
- Target publish date range and timezone
- Optional cadence preference (e.g., daily, 3x/week)

### Outputs
- Recommended publish datetime
- Content slot label (e.g., morning/afternoon/evening)
- Primary KPI objective tag (reach/saves/shares/watch-through)
- Platform metadata package (caption, hashtags, thumbnail text, hook text)

### Acceptance criteria
1. Metadata includes timezone-aware publish datetime in ISO-8601 format.
2. Each item includes one explicit KPI objective tag from the allowed set.
3. Output contains all required fields needed by a downstream scheduler API payload.
4. No direct publish API call is made by MVP workflows.
5. For a batch of 7 items, all metadata objects are generated in one request with no schema violations.

## 3.4 Feature D: Performance Ingestion

### Description
Ingest post-level performance metrics and expose them for analysis and future prompt/context enrichment.

### Inputs
- Post identifier
- Observation window (e.g., 24h, 7d)
- Metric payload (manual CSV upload or API response object)

### Outputs
- Normalized metric record per post
- Derived engagement metrics
- Success/failure label by KPI thresholds

### Required ingested metrics
- Impressions
- Plays/views
- Average watch time (or watch-through proxy)
- Likes
- Comments
- Shares
- Saves
- Follower change attributable window (if available)

### Acceptance criteria
1. System accepts both CSV upload and JSON/API-like payload ingestion paths.
2. Invalid rows are rejected with row-level error details; valid rows continue processing.
3. At least these derived fields are computed when inputs exist: engagement rate, save rate, share rate, watch-through estimate.
4. Ingested records are queryable by post ID and date range.
5. Ingestion run outputs a summary report with counts: processed, succeeded, failed.

---

## 4) MVP KPIs (Measurable)

The MVP is evaluated against measurable account-level and content-level KPIs:

1. **Watch-through rate (WTR)**
   - Definition: completed views / total plays (or proxy formula when completion unavailable)
2. **Save rate**
   - Definition: saves / plays
3. **Share rate**
   - Definition: shares / plays
4. **Follower growth rate**
   - Definition: (followers_end - followers_start) / followers_start over period
5. **Idea-to-publish throughput**
   - Definition: number of generated ideas converted into scheduled metadata per week

### KPI minimum instrumentation acceptance
- Each ingested post record must map to at least one primary KPI objective.
- Dashboard/export layer (even if CLI/JSON) must expose KPI values per post and per week.

---

## 5) Non-goals for MVP

The following are explicitly out of scope for MVP:

1. **Autonomous posting/publishing** to Instagram or Meta APIs when policy/compliance risk is unresolved.
2. Fully autonomous account operation without human review checkpoints.
3. Multi-platform expansion (TikTok/YouTube Shorts/etc.).
4. Automated creative asset rendering (video editing pipeline, voice cloning, generative avatars).
5. Revenue optimization modules (brand deal automation, affiliate funnel optimization).

---

## 6) Cross-feature Acceptance Requirements

1. **Traceability:** every artifact (idea, script, metadata, metric record) has stable IDs and source links.
2. **Schema validation:** all feature outputs pass defined schema checks before persistence.
3. **Deterministic retries:** failed generation/ingestion jobs can be retried with idempotent behavior.
4. **Auditability:** each run logs timestamp, input summary, model/prompt version, and outcome status.

---

## 7) MVP Definition of Done

MVP is complete when:
1. All four MVP features in section 2 are implemented end-to-end.
2. Every acceptance criterion in section 3 is testable and passes in local validation runs.
3. KPI fields in section 4 are populated from ingested data for at least one sample dataset.
4. Non-goal constraints in section 5 are enforced (especially no autonomous posting).


## 8) Publish Safety Enforcement (Production Loop)

To enforce section 5 non-goals while keeping a controlled live-publish escape hatch, the production loop applies hard publish gates:

1. `ALLOW_AUTONOMOUS_PUBLISH=false` by default, which forces simulation payloads even when Instagram credentials are present.
2. Live publish path is only allowed when **all** governance signals are present: `ALLOW_AUTONOMOUS_PUBLISH=true`, `PUBLISH_APPROVAL_GRANTED=true`, and `GOVERNANCE_APPROVED=true`.
3. If any gate is missing, publish stage returns a simulated payload and includes a blocking reason for auditability.
4. This behavior is covered by automated tests for default simulation, explicit override, and blocked-without-approval paths.
