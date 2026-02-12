# Shadow Testing Protocol

## Objective

Select the highest-upside variant before broad distribution while controlling false positives.

## Experiment Design

- Run A/B/n among variants from the same idea family.
- Use comparable audience cohorts or burner accounts with similar baseline behavior.
- Maintain identical posting conditions when possible (time window, hashtag policy).

## Observation Windows

- Early read: 30 minutes
- Primary decision window: 60 minutes
- Optional confirmation: 3 hours for close calls

## Metrics

### Primary
- Normalized view velocity
- Saves+shares per view

### Secondary
- Comment quality score
- Retention/loop proxy
- Profile action rate

## Winner Selection

1. Rank by weighted primary metric.
2. Apply minimum signal threshold (impressions/views floor).
3. Use secondary metrics as tie-breakers.
4. If confidence is low, defer and continue observation.

## Promotion Workflow

- Winner is promoted to main account schedule slot.
- Runner-up can be repurposed for repost/story amplification.
- Log decision rationale and confidence for learning loop.

## Statistical Safety

- Enforce minimum sample size before declaring winner.
- Use shrinkage toward cohort baseline on small samples.
- Track false-positive rate weekly and adjust thresholds.
- Abort test if policy/safety violations occur.
