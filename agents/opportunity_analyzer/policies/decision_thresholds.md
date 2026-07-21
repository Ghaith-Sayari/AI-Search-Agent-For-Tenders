# Opportunity Analyzer — Decision Thresholds Policy

## Purpose
Translate computed score + confidence + blocker state into a final status.

## Thresholds (v1.0)

- `good_fit_min = 75`
- `needs_review_min = 50`
- `not_fit_max = 49.99`
- `min_for_auto_decision = 0.65` (confidence gate)

## Primary decision rules

1. **Blocker first**
   - If confirmed hard blocker and reject mode enabled → `not_fit`
   - If blocker is uncertain → `needs_review`

2. **Confidence gate**
   - If confidence `< min_for_auto_decision` → `needs_review`
   - Even when score is high, low confidence cannot auto-approve.

3. **Score band mapping**
   - If score `>= 75` → `good_fit`
   - If score `>= 50` and `< 75` → `needs_review`
   - If score `< 50` → `not_fit`

4. **Boundary safety**
   - If score is within ±3 points of any threshold, prefer `needs_review`.

## Final status precedence (highest first)
1. Hard blocker outcome
2. Confidence gate
3. Score threshold band
4. Boundary safety override

## Recommended rationale templates
- `good_fit`: “High domain/geography alignment with no hard blockers.”
- `needs_review`: “Borderline score or low confidence; manual validation required.”
- `not_fit`: “Hard blocker found and/or score below viable threshold.”

## Change management
- Threshold updates require policy version bump.
- Keep backward traceability in audit records via `policy_version`.
