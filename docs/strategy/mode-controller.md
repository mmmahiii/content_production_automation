# Creativity Mode Controller

## Modes

- **Exploit:** low variance, high confidence replication.
- **Explore:** medium-high variance, adjacent novelty search.
- **Mutation:** mutate known winners on pacing/framing/emotional angle.
- **Chaos:** unconstrained creativity for breakthrough discovery.

## State Inputs

- 7-day hit rate
- Novelty fatigue index
- Account volatility score
- Model confidence trend
- Monetization quality drift

## Transition Policy (State Machine)

- Start in `Exploit` when confidence is high and hit-rate stable.
- Move `Exploit -> Explore` when novelty fatigue rises above threshold.
- Move `Explore -> Mutation` when one concept family wins repeatedly.
- Move to `Chaos` only when plateau persists for N cycles and risk budget allows.
- Return to `Exploit` after chaos if no top-decile lift in 48 hours.

## Exploration Coefficient

`explore_coef(t+1) = clamp(explore_coef(t) + alpha*(target_regret - observed_regret) - beta*drawdown, min, max)`

- Increase coefficient after missed-opportunity signals.
- Decrease coefficient when performance drawdown exceeds tolerance.
- Example action: reduce by 12% for next 48h after exploratory underperformance.

## Budget and Risk Constraints

| Mode | Max daily posts | Variant count per idea | Promotion threshold | Auto-stop |
|---|---:|---:|---:|---|
| Exploit | 3 | 1-3 | Medium | two consecutive low-signal posts |
| Explore | 2 | 3-6 | Medium-high | 24h drawdown > threshold |
| Mutation | 2 | 4-8 | Medium-high | no uplift across 3 iterations |
| Chaos | 1 | 6-10 | High | immediate stop if safety or severe drawdown triggers |

## Cooldowns

- Minimum 12h before re-entering Chaos.
- Minimum 6h before switching modes more than once.
