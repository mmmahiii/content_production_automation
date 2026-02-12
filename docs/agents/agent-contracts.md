# Agent Contracts and Boundaries

## 1) Creative Director AI
- **Allowed inputs:** trend briefs, mode constraints, brand guardrails, risk budget, monetization goals.
- **Prohibited inputs:** raw generation prompts intended for downstream storytellers.
- **Required outputs:** creative brief with aesthetic, pace, emotional target, and variant budget.
- **Quality rubric:** strategic coherence, novelty intent, brand fit.
- **Escalation:** if confidence < 0.6, request additional intelligence summary.

## 2) Script & Concept Generator
- **Allowed inputs:** creative brief only (no direct trend telemetry).
- **Prohibited inputs:** live trend scores, cluster IDs, engagement metrics.
- **Required outputs:** hook options, narrative arc, overlays, caption+CTA variants.
- **Quality rubric:** clarity in first 2 seconds, narrative tension, CTA naturalness.
- **Escalation:** if unable to produce 3 distinct hooks, request revised brief.

## 3) Visual Generation Agent
- **Allowed inputs:** approved scripts, aesthetic constraints, format specs.
- **Prohibited inputs:** account credentials, posting schedules.
- **Required outputs:** render-ready assets + edit metadata for each variant.
- **Quality rubric:** visual consistency, readability, timing fidelity.
- **Escalation:** route unusable outputs to re-render queue.

## 4) Posting Strategy Agent
- **Allowed inputs:** variant metadata, timing windows, policy constraints.
- **Prohibited inputs:** deep model weights or hidden learning internals.
- **Required outputs:** posting plan (time, hashtags policy, caption length, seeding notes).
- **Quality rubric:** execution safety, strategic fit, schedule efficiency.
- **Escalation:** fail closed on auth/policy errors.

## 5) Feedback & Learning Agent
- **Allowed inputs:** observed metrics, prior predictions, experiment results.
- **Prohibited inputs:** direct override of safety constraints.
- **Required outputs:** parameter deltas, confidence changes, mode-controller recommendations.
- **Quality rubric:** calibration quality, stability, traceability.
- **Escalation:** freeze adaptive updates on anomaly detection.
