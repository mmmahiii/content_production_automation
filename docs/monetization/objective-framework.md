# Dual-Objective Framework: Growth + Monetization

## KPI Hierarchy

1. **Reach Quality:** qualified views in target audience.
2. **Retention & Trust:** saves, shares, return viewers.
3. **Conversion Intent:** intent comments, profile actions, link taps.
4. **Revenue Proxy:** affiliate clicks, DM purchase inquiries, offer page CTR.

## Leading Indicators

- Saves-to-follower ratio
- Intent-comment rate (`where from`, `link?`, `price?`, etc.)
- Story tap-forward/back ratio
- Profile visit to follow conversion

## Objective Function

`TotalObjective = w_g * GrowthScore + w_m * MonetizationScore`

- Start weights: `w_g=0.65`, `w_m=0.35`.
- Increase `w_m` as audience-product fit confidence rises.

## Trade-off Policy

When viral lift harms buyer quality:
- Detect via decline in intent signals despite high reach.
- Reduce broad-trend exploit frequency.
- Prioritize formats with stronger saves and intent density.

## Audience Drift Tracking

Monitor weekly:
- Segment composition changes
- Engagement quality by segment
- Monetization propensity by segment

If drift exceeds threshold, trigger strategy correction:
- Update Creative Director brief constraints.
- Adjust mode-controller toward Explore/Mutation in high-intent segments.
- Rebalance content mix by segment value density.
