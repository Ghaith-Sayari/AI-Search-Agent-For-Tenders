# Expired tender policy

Policy version: 1.0

A tender is `expired` when any of the following is true:

- its extracted submission deadline is before the processing date;
- the record or source page explicitly states that the procurement was closed,
  cancelled, awarded, or withdrawn; or
- the tender is otherwise clearly unavailable for new submissions.

## Deadline handling

- Preserve the raw deadline value from staging.
- Store the parsed value as `extracted_deadline` when it can be determined
  reliably.
- Do not approve a tender with no reliably extracted future deadline.
- If the tender appears legitimate but its deadline is missing or ambiguous,
  route it to `needs_review` unless explicit closure evidence is present.
