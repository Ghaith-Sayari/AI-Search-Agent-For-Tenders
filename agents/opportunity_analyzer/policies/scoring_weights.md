# Opportunity Analyzer — Scoring Weights Policy

## Purpose
Define how total opportunity fit score is calculated.  
All sub-scores are normalized to **0..100** and combined by weighted sum.

## Current weight set (policy v1.0)

| Dimension | Weight | Meaning |
|---|---:|---|
| Domain relevance | 0.35 | How well scope/services match our core capabilities |
| Geography fit | 0.20 | How well location/country aligns with target markets |
| Budget fit | 0.20 | How well estimated budget matches our commercial band |
| Eligibility fit | 0.15 | How well eligibility/certification/legal conditions match us |
| Strategic fit | 0.10 | How well tender aligns with strategic priorities |

**Constraint:** sum of all weights must equal **1.00**.

## Formula

`total_score = Σ (dimension_score * dimension_weight)`

Where:
- `dimension_score ∈ [0, 100]`
- `dimension_weight ∈ [0, 1]`

Result:
- `total_score ∈ [0, 100]`

## Sub-score guidance

### 1) Domain relevance (0.35)
- 90–100: Core services exactly requested.
- 70–89: Strong overlap with minor gaps.
- 40–69: Partial overlap, significant uncertainty.
- 0–39: Low overlap.

### 2) Geography fit (0.20)
- 100: Target country/region and delivery feasible.
- 60–80: Nearby or feasible with manageable overhead.
- 0–50: Non-target geography or major operational friction.

### 3) Budget fit (0.20)
- 90–100: In preferred range.
- 60–80: Slightly above/below preferred, still viable.
- 0–50: Far outside economic viability band.

### 4) Eligibility fit (0.15)
- 100: All mandatory legal/certification criteria satisfied.
- 50–90: Minor resolvable documentation gaps.
- 0–40: Missing hard mandatory criteria.

### 5) Strategic fit (0.10)
- 80–100: Strongly aligned with current growth priorities.
- 40–79: Useful but not a priority.
- 0–39: Distracts from strategic direction.

## Tie-break and safety notes
- If hard filters are triggered, hard-filter policy takes precedence over score.
- If score is near threshold (±3 points), route to manual review.
- If confidence is below `min_for_auto_decision`, route to review even with high score.
