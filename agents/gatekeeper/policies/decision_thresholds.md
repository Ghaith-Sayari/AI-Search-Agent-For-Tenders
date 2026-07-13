# Decision and confidence thresholds

Policy version: 1.0

The Gatekeeper records a confidence score from 0.00 to 1.00 for every
decision. The score measures confidence in the classification, not the
commercial value of the tender.

## Automatic decisions

- `approved`: confidence must be at least 0.85 and all valid tender criteria
  must be satisfied.
- `rejected`: confidence must be at least 0.85 and there must be clear junk or
  non-procurement evidence.
- `expired`: confidence must be at least 0.85 and there must be a past
  deadline or explicit closure evidence.

## Review decisions

- Use `needs_review` for confidence from 0.60 to 0.84.
- Use `needs_review` below 0.60 unless deterministic evidence proves the page
  is junk or expired.
- Use `failed` only for technical failures, invalid model output, or processing
  errors; it is not a business classification.

Every decision must include a concise, evidence-based reason suitable for
audit and human review.
