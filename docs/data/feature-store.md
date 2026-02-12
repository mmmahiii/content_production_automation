# Feature Store Policy

## Time-Decay Weighting

Use exponential decay for historical examples:

`weight(age_days) = exp(-lambda * age_days)` where `lambda` defaults to `0.08`.

- Half-life ~8.7 days.
- Per-niche tuning allowed within `[0.05, 0.12]` based on volatility.

## Feature Freshness

- **Hot features (velocity/audio trend/sentiment):** refresh every 15 minutes.
- **Warm features (cluster assignments/creator consistency):** refresh hourly.
- **Cold features (audience composition priors):** refresh daily.

Feature TTLs:
- Hot: 2 hours
- Warm: 24 hours
- Cold: 7 days

Expired features trigger fallbacks to latest valid snapshot + confidence penalty.

## Missing Data / Backfill

1. Mark missing source fields as `null` in raw events.
2. Impute only in derived feature layer using per-niche medians or model-based estimates.
3. Persist `imputation_method` and `imputation_confidence` with each feature.
4. Recompute backfilled windows when delayed data arrives (up to 72 hours).

## Governance

- Feature definitions are versioned.
- Model training jobs pin a feature version.
- Breaking feature changes require migration notes and shadow validation.
