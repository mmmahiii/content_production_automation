# Virality Dataset Specification

## Canonical Record

Each reel observation is represented as a canonical row keyed by `(platform, reel_id, observed_at_bucket)`.

### Required Fields

- `reel_id` (string): unique reel identifier.
- `niche` (enum/string): primary cluster (`fashion`, `couple`, `lifestyle`, `pov`, `luxury`, `other`).
- `hook_type` (string): first 1-2 second framing category.
- `audio_id` (string): audio track identifier.
- `caption_style` (string): taxonomy label (e.g., `minimal`, `question`, `story`, `listicle`).
- `visual_structure` (string): shot/edit pattern classification.
- `posting_time` (datetime UTC): original publish timestamp.
- `growth_curve` (object): normalized timeseries points (1h/3h/6h/24h views, likes, comments, saves, shares).
- `outcome_score` (float 0-100): normalized performance target.

### Optional Fields

- `creator_id`, `creator_tier`, `follower_count_bucket`
- `reach`, `impressions`, `loop_rate_estimate`, `view_velocity_1h`, `view_velocity_3h`
- `sentiment_score`, `top_comment_keywords`
- `hashtag_count`, `caption_length`, `text_overlay_density`
- `country_mix`, `language`, `content_safety_flags`

## Data Types and Constraints

- All rates are non-negative.
- Missing raw metrics are represented as `null`, never zero-filled in raw table.
- `growth_curve` supports sparse timepoints but must include at least one early window (`<=3h`).
- `outcome_score` is only assigned after minimum 24h observation or extrapolation confidence >= 0.8.

## Source of Truth

- Scraper: views, likes, comments, saves/shares proxies, caption, visual transcript.
- IG Graph API: account-level metadata, reach/impressions where available.
- Inference pipeline: hook type, visual structure, sentiment, keyword entities.
- Audio cross-platform feed: trend momentum and crossover index.

## `outcome_score` Definition

Suggested weighted objective:

- Early momentum (30%): percentile rank of 1h/3h velocity in niche cohort.
- Engagement quality (25%): weighted saves+shares over views.
- Retention proxy (20%): loop-rate estimate and completion proxies.
- Conversation pull (15%): comment rate adjusted by sentiment quality.
- Durable tail (10%): 24h-48h sustained growth slope.

Scores are normalized per niche and posting-time bucket to reduce structural bias.
