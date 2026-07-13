# Gatekeeper policies

These documents define the business rules applied before an opportunity enters
the production dataset. The current policy version is **1.0**.

Policies are deterministic requirements. The Gatekeeper may use semantic
reasoning to interpret a record, but it must not override an explicit policy.

Any policy change must increment the policy version recorded in each
Gatekeeper decision.
