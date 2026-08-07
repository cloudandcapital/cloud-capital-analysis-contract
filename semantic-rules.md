# Semantic Rules Beyond JSON Schema

JSON Schema validates shape. The conformance library must also enforce reference integrity and financial semantics.

## Identity and reference rules

- IDs are unique within each catalog and stable for the same logical object across reruns when source identity is stable.
- Every `evidence_id`, `metric_id`, `finding_id`, `opportunity_id`, aggregate ID, and input metric ID resolves.
- Evidence source IDs resolve to declared inputs.
- Producer on every opportunity matches the containing result producer.
- All artifacts in a run share run ID, mode, and compatible periods.

## Numeric rules

- No NaN or infinity.
- Currency calculations use decimal semantics; serialization uses JSON numbers and comparison uses declared currency minor-unit tolerance.
- Estimate range satisfies `low <= expected <= high`.
- Reconciliation passes only when `abs(difference) <= tolerance`.
- A calculated/allocated/estimated metric's referenced inputs and formula are present.
- `null` requires basis `unknown`, an unknown reason, and a quality issue when material.
- A parser exception or absent field cannot emit a valid observed/calculated zero.

## Period and scope rules

- Period start precedes period end.
- Additive sums require matching currency and compatible periods.
- Scopes must be disjoint or explicitly allocated before addition.
- `non_additive`, `ratio`, and incompatible `semi_additive` metrics cannot enter additive totals.
- Resilience scenario cost is not added to technology spend unless it represents observed billed cost already reconciled in FinOps Lite; modeled alternative cost remains a scenario metric.

## Trust rules

- `unattributed_cost` cannot be an opportunity estimate solely because it is unattributed.
- Only a `verified_outcome` may contain basis `verified` for a realized financial result.
- Opportunity review flags are all true.
- Review steps are non-mutating descriptions/queries only; block cloud/API commands containing mutation verbs or known mutating operations.
- Public/illustrative artifacts cannot contain live account IDs, resource IDs, credentials, secrets, or customer-identifying values.
- An opportunity with `potential`, `nested`, or `exclusive` overlap is excluded until the aggregate applies a valid rule.
- Aggregate opportunity IDs and reverse membership reconcile.

## Report rules

- Every display reference resolves.
- Every headline number traces through metric evidence to source hashes.
- A complete report includes all five analytical producer results; Command Center is the report producer.
- A partial report explicitly lists omissions and does not present an all-in total unless its label names the included scopes.
- Illustrative disclosure is visible and machine-readable.
- All reconciliation entries pass before status can be `complete`.

