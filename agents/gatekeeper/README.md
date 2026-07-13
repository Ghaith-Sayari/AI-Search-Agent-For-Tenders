# Gatekeeper

The Gatekeeper protects the production dataset. It removes junk pages, cleans
scraped content, extracts essential procurement data, and decides whether an
opportunity is approved, rejected, or requires review.

Its intended flow is:

1. Clean the normalized record.
2. Extract missing structured information.
3. Apply business policies.
4. Classify the opportunity.
5. Record the decision for auditability.
