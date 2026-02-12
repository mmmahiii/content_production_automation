# Virality Score Operational Definition

## Formula

`score = Novelty * PatternStrength * EmotionalPull * PlatformBias * CreatorConsistency`

Each component is normalized to `[0.2, 1.2]` to avoid hard-zero collapse and permit controlled amplification.

## Component Proxies

### 1. Novelty
- Inputs: embedding distance from recent successful cluster centroids, concept rarity in last 14 days.
- Normalization: higher distance and rarity increase score until saturation threshold.
- Confidence: reduced when embedding coverage is sparse.
- Sparse fallback: set to cohort median with -15% confidence penalty.

### 2. PatternStrength
- Inputs: cluster momentum, trend acceleration, survival of similar formats over 7 days.
- Normalization: percentile within niche/time bucket.
- Confidence: tied to sample size and recency.
- Sparse fallback: use rolling 30-day baseline.

### 3. EmotionalPull
- Inputs: hook sentiment tension score, expected curiosity gap, prior comment intensity for similar narratives.
- Normalization: calibrated against historical engagement quality.
- Confidence: decreases when narrative parser confidence < 0.7.
- Sparse fallback: storytelling prior by hook family.

### 4. PlatformBias
- Inputs: current format preference signals (audio-heavy vs text-led, average reel length band performance).
- Normalization: weighted blend of global and niche-specific bias.
- Confidence: lowered during platform update anomalies.
- Sparse fallback: prior-week platform state.

### 5. CreatorConsistency
- Inputs: alignment to creator's established aesthetic and audience expectation profile.
- Normalization: cosine similarity to creator signature vector.
- Confidence: low for new accounts.
- Sparse fallback: neutral value `1.0` with uncertainty flag.

## Decision Thresholds

- `<0.45`: kill idea.
- `0.45 - 0.70`: generate 1 conservative variant.
- `0.70 - 0.95`: generate 3-5 variants.
- `>=0.95`: generate 8-10 variants + mandatory shadow testing.

## Calibration Loop

- Refit cadence: weekly full calibration + daily lightweight bias correction.
- Metrics:
  - MAE on predicted vs actual normalized outcome
  - Top-decile precision (how often predicted winners are actual winners)
  - Regret vs oracle (missed opportunity estimate)
- Guardrails:
  - Cap weekly parameter drift per factor.
  - Require out-of-sample lift before promoting new model.
  - Freeze updates during detected data quality incidents.
