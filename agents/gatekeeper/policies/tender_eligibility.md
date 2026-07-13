# Valid tender criteria

Policy version: 1.0

An opportunity can be approved only when it is a genuine procurement notice
and contains sufficient information for a user to assess and pursue it.

## Required evidence

The record must provide, either directly or through its cleaned description:

- a procurement context, such as a tender, request for proposals, invitation
  to bid, call for tenders, or comparable purchasing process;
- a clear scope of work, goods, services, or project to be procured;
- an identifiable buyer, contracting authority, funder, or issuing
  organization;
- a valid future submission deadline that can be extracted into a structured
  date; and
- enough useful procurement information to distinguish the opportunity from a
  generic landing page.

## Decision rules

- Approve only when all required evidence is present and the tender is active.
- Send to `needs_review` when the record appears to be a tender but one or
  more required details are missing or ambiguous.
- Reject when the page is clearly not a procurement opportunity.
- Mark as `expired` when it is a real tender but is no longer active.
