# Phase 0 Decisions

## ADR: accounting boundaries are `ccac/1.1.0`

Accounting-boundary semantics are an opt-in minor contract version, not an undocumented reinterpretation of `ccac/1.0.0`. Validator dispatch uses the declared contract and a distinct packaged schema set; unsupported versions fail closed. Existing 1.0 artifacts retain their original schemas and behavior.

Billing-channel classification makes provider-billed native AI `cloud`, direct vendor AI `direct_ai`, and SaaS exclusive of direct-AI vendors. A combined total is valid only after the three producer-owned values pass eligibility and reconciliation. This decision introduces no producer calculation or dashboard integration.

## Frozen for implementation

1. The public contract name is `CCAC`, Cloud & Capital Analysis Contract.
2. The first stable contract will be `ccac/1.0.0`; this package is design draft `1.0.0-draft.1`.
3. JSON Schema 2020-12 validates structure; a shared semantic validator enforces references and financial trust rules.
4. FOCUS remains the normalized billing foundation but is not overloaded to represent findings, opportunities, workflows, or verified outcomes.
5. Tech Spend Command Center is the sole trusted-report producer and owns no domain estimate formula.
6. Tool results, trusted reports, and verified outcomes are separate document types.
7. Real-data v1 is local-file, read-only, credential-free, and network-free by default.
8. Public demo data uses the same engines and schemas as real mode and is explicitly illustrative in every artifact.
9. Unknown is distinct from zero. A missing value must fail or remain null with a reason.
10. The pipeline fails closed. Partial output requires an explicit user choice and visible omissions.
11. Opportunity estimates use ranges, not a single falsely precise value alone.
12. No opportunity can be implemented or verified inside the public analysis pipeline.
13. Cloud Cost Guard remains unchanged until a complete trusted report passes conformance.

## Compatibility policy

- Major: breaking schema or semantic change.
- Minor: backward-compatible optional capability; consumers must ignore only explicitly permitted extension fields.
- Patch: clarification or validator correction that does not change valid document meaning.
- Every artifact states exact contract version and producer version.
- Consumers reject unsupported major versions; supported minor versions are declared in a compatibility matrix.

## Decisions required immediately before coding

These are bounded engineering choices, not product-strategy questions:

1. Host the pipeline CLI in `ccac` or Tech Spend Command Center. Recommendation: `ccac` initially, keeping Command Center a pure aggregator library/CLI.
2. Support only Python validator in the first milestone or ship Python and JavaScript together. Recommendation: Python first; generate/validate the same JSON Schema in Cloud Cost Guard later.
3. Decimal serialization policy. Recommendation: JSON numbers plus ISO currency, with Decimal arithmetic internally and explicit tolerance; avoid string-money ergonomics in v1.
4. End-date semantics. Recommendation: start inclusive, end exclusive; encode this explicitly before fixtures are finalized.
5. FOCUS conversion dependency. Recommendation: benchmark and test the FinOps Foundation converter before deciding embed versus optional adapter.

## Explicitly deferred

- Live cloud credentials/connectors.
- Shared database or hosted control plane.
- Autonomous remediation.
- Enterprise SSO/RBAC, notifications, ITSM, and scheduled hosted runs.
- Automatic FX conversion.
- LLM-generated domain calculations.
- Cloud Cost Guard redesign.
