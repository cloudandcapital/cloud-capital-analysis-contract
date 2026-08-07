# End-to-End Acceptance Suite

## Test profile

The first conformance profile is `illustrative-complete-v1`. It runs without credentials or network access from versioned source fixtures. The semantic output must be deterministic; volatile `run_id` and timestamps are normalized only for golden-file comparison.

```text
illustrative sources
  -> FinOps Lite canonical ledger/result
  -> Watchdog result
  -> Recovery Economics result
  -> AI Cost Lens result
  -> SaaS Cost Analyzer result
  -> Command Center trusted report
  -> existing Cloud Cost Guard only after report conformance passes
```

Recovery, AI, and SaaS may consume their own domain fixtures plus FinOps Lite references. Watchdog consumes canonical metrics. Command Center consumes results only; it never executes producer formulas.

## Required golden scenario

The scenario must contain:

- AWS FOCUS 1.2, Azure FOCUS, and Google FOCUS/native representative rows.
- Positive charges, credits, a refund, an amortized commitment, provider extension fields, an untagged row, and a late adjustment.
- A Kubernetes/OpenCost allocation that is explicitly non-additive to cloud total.
- At least 35 daily observations, one injected spike, one new-spend series, and one insufficient-history series.
- Two resilience alternatives with RTO/RPO targets, incremental/full assumptions, restore costs, and one stale restore test.
- AI requests with input/output/cached tokens, vendor-reported cost, calculated cost, one unsupported model, one failed request, and one session outcome metric.
- SaaS invoices, entitlements, assignments, active/inactive/unknown activity, a renewal date, a consumption-priced product, and a duplicate-category candidate.
- At least one independent, one exclusive, one nested, and one potentially overlapping opportunity.

Golden expected values must be calculated in a checked-in worked-example document, not copied from tool output after implementation.

## Structural acceptance assertions

| ID | Assertion | Expected behavior |
|---|---|---|
| S-001 | Every artifact declares `ccac/1.0.0`, producer name/version, run ID, mode, period, sources, quality, and hashes. | Invalid document exits nonzero. |
| S-002 | IDs are unique within type and references resolve. | Duplicate/dangling ID fails. |
| S-003 | Required fields are not supplied through parser defaults. | Missing field fails. |
| S-004 | Unsupported contract major version is supplied. | Consumer fails with compatibility error. |
| S-005 | Unknown field appears where `additionalProperties` is false. | Validation fails. |
| S-006 | Tool output and manifest run IDs differ. | Pipeline fails. |
| S-007 | Artifact hash differs from manifest. | Pipeline fails before aggregation. |

## Financial and semantic assertions

| ID | Assertion | Expected behavior |
|---|---|---|
| F-001 | Cloud provider totals equal normalized ledger total within currency tolerance. | Reconciliation passes or report is invalid. |
| F-002 | Credits and refunds preserve sign. | Negative amounts remain negative. |
| F-003 | Missing/unparseable amount is encountered. | `null` + reason/quality issue; never zero. |
| F-004 | Multiple currencies are present without an approved FX table. | Separate currency totals; no combined currency total. |
| F-005 | Kubernetes allocated view is present. | Displayed, traceable, excluded from combined spend. |
| F-006 | Untagged spend exists. | Classified as unattributed cost, not an opportunity. |
| F-007 | Derived metric is displayed. | Formula, input metric IDs, and evidence resolve. |
| F-008 | An estimate is produced. | Basis remains `estimated`; no verified-savings field exists in a tool result. |
| F-009 | Verified outcome is claimed. | Separate valid verified-outcome document with approval, implementation, baseline, post-change evidence, and verification window is required. |

## Domain assertions

| ID | Domain | Assertion |
|---|---|---|
| D-001 | Watchdog | Robust baseline identifies the injected spike and publishes observed, expected range, delta, materiality, method, history window, and contributors. |
| D-002 | Watchdog | New spend and insufficient history are distinct states. Zero standard deviation does not crash or silently suppress a material new series. |
| D-003 | Recovery | Scenario arithmetic reconciles storage, request, retrieval, compute, egress, and other declared components. |
| D-004 | Recovery | RTO/RPO compliance without current restore-test evidence cannot be labeled verified recoverability. |
| D-005 | AI | Vendor-reported and price-book-calculated costs remain distinct; variance is visible. |
| D-006 | AI | Unsupported model pricing produces unknown cost and a quality issue, not `$0`. |
| D-007 | SaaS | Missing activity produces `unknown`; inactive requires a defined threshold and activity evidence. |
| D-008 | SaaS | Reclaim estimate is derived only from eligible inactive assignments and declared seat allocation; consumption-priced products are excluded from seat math. |
| D-009 | Command Center | Actual FinOps Lite, Watchdog, Recovery, AI, and SaaS contract fixtures parse without adapter-specific heuristics. |
| D-010 | Command Center | Command Center originates no domain opportunity amount. |

## Overlap and trust assertions

| ID | Assertion | Expected behavior |
|---|---|---|
| T-001 | Two `exclusive` opportunities in one overlap group are selected. | Aggregate fails. |
| T-002 | `potential` overlap is unresolved. | Excluded by default and listed with reason. |
| T-003 | Aggregate amount differs from included opportunity sum. | Reconciliation fails. |
| T-004 | Opportunity contains a mutating public command. | Contract/semantic validation fails. |
| T-005 | Report display references a missing metric/finding/aggregate. | Report fails. |
| T-006 | Illustrative report lacks a visible illustrative disclosure. | Report fails. |
| T-007 | Complete report omits a required producer. | Report fails; explicit partial mode is required. |
| T-008 | Partial report is allowed by explicit CLI option. | Omitted producers and impact are prominent; combined totals cannot imply full coverage. |
| T-009 | Lumen quotes an amount absent from canonical metrics or aggregates. | Lumen response validation rejects it/falls back to source-grounded wording. |

## Fresh-install acceptance

Each repository must pass in a clean environment:

1. Build/install from declared package metadata.
2. `--help` and `--version` with a read-only home directory and no network.
3. `demo` in under five minutes without credentials.
4. `validate` and `analyze` against its fixtures.
5. Invalid input exits nonzero with a stable error code and useful message.
6. JSON sent to stdout is not contaminated by progress/log text.
7. Docker image runs as non-root with a read-only root filesystem and writable output mount.
8. README commands are executed in CI rather than copied as untested prose.

## Pipeline exit contract

- `0`: complete, contract-valid run.
- `2`: user/input/validation failure.
- `3`: producer execution failure.
- `4`: compatibility or artifact-integrity failure.
- `5`: reconciliation or trust-rule failure.
- `6`: explicitly requested partial report produced; usable but never interpreted as complete.

No “findings exist” exit code is used in the pipeline; findings are valid analytical output, not execution failure.

