# Content Feedback Loop

This document defines how post-level performance data is collected, normalized, scored, and fed back into content generation.

## 1) Per-post metrics collected

For every published post, the system records the following platform-native metrics:

- **Views**: Total play/impression count.
- **Retention**: Audience retention percentage at standardized checkpoints (for example: 3s, 50%, 95%, completion), plus average watch time when available.
- **Likes**: Total likes/reactions.
- **Comments**: Total comments.
- **Shares**: Total shares/reposts.
- **Saves**: Total bookmarks/saves.
- **Profile visits**: Profile visits attributed to the post.

Where platform APIs expose additional dimensions (traffic source, geography, audience segment), those are stored as optional metadata and do not replace the required core metrics above.

## 2) Pull and normalization cadence

### Data pull schedule

Data is pulled in two phases:

1. **Rapid phase (early signal):** every 6 hours for the first 72 hours after publish.
2. **Mature phase (long-tail signal):** daily from day 4 through day 30.

After day 30, posts are sampled weekly for archival trend analysis.

### Normalization process

Each pull produces a `PerformanceSnapshot` that is normalized as follows:

- Metric names are mapped to canonical fields (`views`, `retention`, `likes`, `comments`, `shares`, `saves`, `profileVisits`).
- Missing values are stored as `null` and excluded from ratio-based scoring terms.
- Engagement counts are transformed into rates when possible:
  - `likeRate = likes / views`
  - `commentRate = comments / views`
  - `shareRate = shares / views`
  - `saveRate = saves / views`
  - `profileVisitRate = profileVisits / views`
- Retention is converted to a normalized 0–1 range.
- Extreme outliers are winsorized at the 99th percentile per platform and content format.
- A platform+format baseline z-score is computed for each normalized metric to allow cross-post comparisons.

## 3) Scoring logic for content variants and themes

### Candidate-level score

Each `ContentCandidate` receives a weighted composite score from linked published posts:

- **Primary score** (default weights):
  - 30% retention quality
  - 25% share rate
  - 15% save rate
  - 10% comment rate
  - 10% profile visit rate
  - 10% like rate

Formula (example):

```text
candidateScore = Σ(weight_i * zMetric_i)
```

Where `zMetric_i` is the normalized z-score for the metric term.

### Theme-level score

A theme score is an exponentially weighted moving average (EWMA) across all candidates tagged to that theme:

```text
themeScore_t = α * mean(candidateScores_t) + (1 - α) * themeScore_(t-1)
```

Default `α = 0.35` for moderate responsiveness.

### Confidence-adjusted ranking

To prevent high scores on tiny sample sizes, each candidate/theme rank is multiplied by a confidence factor:

```text
confidence = min(1.0, sqrt(totalViews / targetViews))
rankScore = rawScore * confidence
```

## 4) How scoring updates prompts and generation constraints

Scores update generation behavior in two channels:

1. **Prompt template adaptation**
   - High-scoring hooks, structures, and call-to-action patterns are promoted into the default prompt template.
   - Low-scoring patterns are marked as discouraged and moved to optional/experimental blocks.
   - Theme-specific phrasing tokens are weighted based on recent theme score.

2. **Constraint adaptation**
   - Generation constraints (length range, hook style, CTA intensity, pacing directives) are adjusted within bounded limits.
   - Example: if short-form retention drops, tighten opening hook constraints and reduce intro length.
   - Constraints are never hard-switched from a single post; updates use rolling aggregates and guardrails.

All prompt/constraint updates should be logged with:
- score inputs used,
- prior and new template/constraint values,
- timestamp and model/version metadata.

## 5) Safeguards against short-term noise and overfitting

The system applies the following safeguards before any automatic update is applied:

- **Rolling windows**
  - Fast window: trailing 7 days for quick diagnostics.
  - Stable window: trailing 28 days for update decisions.
  - Stable window has priority when windows disagree.

- **Minimum sample sizes**
  - Candidate-level updates require at least 3 published posts and 5,000 aggregate views.
  - Theme-level updates require at least 5 published posts and 20,000 aggregate views.

- **Change thresholds**
  - Only apply prompt/constraint updates when score deltas exceed a minimum effect size (for example: `|Δz| >= 0.2`).

- **Cooldown periods**
  - At most one automatic template update per theme every 72 hours.

- **Exploration budget**
  - Reserve 10–20% of output for controlled experiments, even when a dominant theme performs best.

- **Human override**
  - Optional manual review gates can block updates during seasonal events, campaigns, or known platform anomalies.
