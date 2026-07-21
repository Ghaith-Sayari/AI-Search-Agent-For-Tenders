# Opportunity Analyzer — Hard Filters Policy

## Purpose
Hard filters are non-negotiable rules.  
If triggered, they can force `not_fit` (or `needs_review`) regardless of score.

## Principle
1. Evaluate hard filters before final decision.
2. If `reject_if_any_blocker=true`, any blocker produces `not_fit`.
3. If blocker detection is uncertain, route `needs_review`.

## Baseline blockers (v1.0)

### Eligibility blockers
- Mandatory certification required but unavailable.
- Mandatory legal structure incompatible with company profile.
- Mandatory documents cannot be produced by deadline.

### Geography blockers
- Mandatory local office in non-target country with no feasible partner model.
- Country is explicitly excluded by policy/compliance.

### Commercial blockers
- Financial guarantees/bid bond above accepted internal risk cap.
- Contract terms contain unlimited liability without acceptable carve-outs.

### Time blockers
- Deadline already passed.
- Remaining submission time below operational minimum to produce quality bid.

## Soft vs hard interpretation
- **Hard blocker:** deterministic, explicit requirement in tender text.
- **Soft blocker (risk):** ambiguous or inferred constraint; should trigger review.

## Output mapping
- Hard blocker confirmed + reject mode ON → `status=not_fit`
- Hard blocker suspected/ambiguous → `status=needs_review`
- No blockers → continue normal score/threshold decision path

## Audit requirements
When a hard filter is triggered, store:
- `blockers[]` list with normalized short labels
- original evidence snippet (if available in classifier output/audit trail)
- policy version used for decision

## Examples
- “Local presence in Country X is mandatory” and Country X not in target footprint → blocker
- “ISO 27001 required at bid submission” and company lacks certification → blocker
- “Deadline: yesterday” → blocker
