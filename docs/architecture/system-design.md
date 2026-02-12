# Adaptive Content Organism: System Design

## Service Map by Layer

| Layer | Service / Module | Inputs | Outputs | Trigger Cadence | Failure Handling | Downstream Dependencies |
|---|---|---|---|---|---|---|
| 1. Data Ingestion | `ingestion-pipeline` | Reels metadata scrapes, IG Graph API responses, audio trend feed, comments | Normalized virality events | Near-real-time (5-15 min polling), hourly compaction | Retry with exponential backoff; mark source stale after 3 failures; dead-letter queue | Feature store, pattern discovery |
| 2. Virality Intelligence | `intelligence-engine` | Virality events, historical feature store, creator profile priors | Pattern reports, score models, idea scoring decisions | Hourly incremental, daily full refresh | Fall back to last healthy model; confidence floor gating | Creative Director, mode controller |
| 3. Creative Generation | `creative-orchestrator` + generation workers | Strategy briefs, score bands, mode constraints, disallowed themes | Variant packages (hook/caption/overlay/video variants) | Event-driven when an idea is approved | If generation job fails, regenerate variant with alternate template; quarantine failed prompt families | Shadow testing, posting engine |
| 4. Testing & Posting | `experiment-and-post` | Variant packages, schedule windows, hashtag/caption policies | Shadow test metrics, promoted post jobs, publishing logs | Shadow launch every approved batch; publish per schedule policy | Cancel jobs on auth or platform errors; retry with jitter; post queue rebalancing | Feedback loop, audit log |
| 5. Feedback Learning | `learning-loop` | Real-time performance metrics, predicted scores, experiment outcomes | Model deltas, exploration coefficient updates, strategy constraints | 15-min incremental, 48-hour policy updates | Freeze adaptive updates on anomaly; roll back to prior model snapshot | Mode controller, intelligence engine |
| 6. Monetization Intelligence | `monetization-analyst` | Audience composition, intent comments, saves/follows, profile actions | Monetization opportunity scores, segment drift alerts, strategy nudges | Daily + weekly strategic review | Hold recommendations when confidence low; request more exploration in affected segment | Creative Director, objective optimizer |

## One Full Cycle Sequence (Text Diagram)

1. `ingestion-pipeline` pulls latest reels, comments, and audio trend signals.
2. Pipeline emits normalized `virality_event` records and writes to the feature store.
3. `intelligence-engine` updates pattern clusters and computes score for candidate ideas.
4. `mode-controller` picks mode (Exploit / Explore / Mutation / Chaos) based on risk and recency performance.
5. `creative-orchestrator` requests structured variants from specialized generators.
6. `experiment-and-post` sends variants to shadow testing accounts/cohorts.
7. After the observation window, experiment service selects winner and promotes to primary distribution.
8. Live performance metrics flow into `learning-loop` for predicted-vs-actual error analysis.
9. `learning-loop` updates model priors and exploration coefficient.
10. `monetization-analyst` updates conversion-intent and audience-quality guidance for next cycle.

## Operational Non-Functional Requirements

- **Observability:** every stage emits latency, error, and confidence metrics.
- **Idempotency:** ingestion and publishing jobs use deterministic keys to prevent duplicates.
- **Auditability:** all strategy decisions and model version references are persisted.
- **Safety:** disallowlist filters apply before generation and before posting.
