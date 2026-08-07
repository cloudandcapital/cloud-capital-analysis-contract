# Repository-by-Repository Implementation Specifications

This is sequencing and acceptance scope, not authorization to edit the repositories.

## 0. New shared contract package

Create `cloudandcapital/ccac` as the only new repository proposed by Phase 0.

**Owns:** schemas, semantic validator, compatibility matrix, Python package, optional JavaScript validator, fixtures, error codes, contract changelog, and conformance CLI.

**Required commands:**

```text
ccac validate <artifact>
ccac validate-run <run-directory>
ccac explain-error <error-code>
```

It must not own domain formulas or execute any cloud action.

## 1. Pipeline harness

Place the initial orchestration entry point in Tech Spend Command Center or a tiny package in the CCAC repository; decide before coding. It writes an immutable run directory, captures versions/hashes, invokes each CLI with explicit files, and stops on invalid output.

**Required commands:**

```text
cc-pipeline demo --output <directory>
cc-pipeline run --config <file> --output <directory>
cc-pipeline validate <directory>
```

No shared database, daemon, credentials, or network requirement in the first release.

## 2. FinOps Lite

**Remove/retire:** unofficial `FOCUS 2026` naming; conflicting FOCUS-lite output families; placeholder recommendation claims; home-directory writes during help/version.

**Add:** FOCUS version declaration; Foundation validator/converter decision; AWS FOCUS 1.2/CUR 2.0, Azure FOCUS, and Google FOCUS/native file adapters; Parquet/CSV streaming; normalized ledger; source/adapter metadata; data quality report; exact reconciliation; allocation and unit-metric rules; CCAC result.

**Compatibility:** preserve provider extensions in namespaced fields. Do not claim native provider support until real representative fixtures pass.

**Gate:** ledger totals reconcile to worked examples including credits/refunds/amortization. `metric.cloud.total` is never silently zero.

## 3. FinOps Watchdog

**Remove/retire:** README/code conflict; arbitrary column mappings as the primary pipeline contract; unconditional-success documentation mismatch.

**Add:** canonical CCAC metric input; robust median/MAD baseline; seasonal baseline with minimum history; new-spend and insufficient-history states; absolute/relative materiality; contributor decomposition; lifecycle status; deterministic CCAC result.

**Gate:** published injected-event fixtures and evaluation report. The algorithm named in documentation is the algorithm executed.

## 4. Recovery Economics

**Remove/retire:** stale command documentation, disconnected static pricing module, committed backup source files, and claims unsupported by the formula.

**Add:** scenario schema; workload criticality; RTO/RPO targets; full/incremental backup semantics; retention/tier/minimum-duration assumptions; compression/deduplication; storage/request/retrieval/compute/egress components; failover/failback; business impact kept separate from vendor cost; restore-test evidence/freshness; ranges and sensitivity; CCAC result.

**Gate:** each scenario contains a worked arithmetic reconciliation. Recoverability is never “verified” without a qualifying test.

## 5. AI Cost Lens

**Remove/retire:** API-key instructions for file-only behavior, absent commands, silent numeric parse-to-zero, and first-row-only provider assumptions.

**Add:** explicit import profiles for provider exports, Langfuse, and LiteLLM; request/session/workflow dimensions; vendor-reported versus calculated cost; versioned price book; input/output/cached/reasoning and supported multimodal units; errors/latency/outcomes; unsupported-price state; budget/forecast interfaces; CCAC result.

**Gate:** price-book snapshots are immutable and dated. Unsupported models produce unknown cost and visible coverage metrics.

## 6. SaaS Cost Analyzer

**Remove/retire:** absent CLI commands in README; missing usage treated as unused; blanket/naive forecasting claims.

**Add:** separate application, contract, invoice, entitlement, assignment, and activity records; configurable inactivity window; unknown activity state; seat versus consumption pricing; renewal/notice/commitment exposure; duplicate-category evidence; reclaim estimate; post-change verified-outcome support; CCAC result.

**Gate:** only evidenced inactive, reclaim-eligible assignments enter seat reclaim estimates. Consumption products never use seat arithmetic.

## 7. Tech Spend Command Center

**Delete:** permissive `_safe_float` coercion for required values, heuristic producer schemas, reconstructed prior spend, generic top-service recommendations, and invented 15% SaaS savings.

**Add:** exact CCAC validation; artifact compatibility/integrity; inclusion/exclusion; overlap groups; deterministic aggregates; partial-report semantics; reconciliation ledger; display references; trusted report; provenance.

**Gate:** hostile fixtures fail for the intended stable error code. Actual outputs from all upgraded producers produce one complete trusted report.

## 8. Cloud Cost Guard and Lumen — last

Do not change until the trusted-report gate passes.

**Then add:** a CCAC report adapter or direct schema consumption; source/basis/freshness drill-through; illustrative/real/partial labels; verified-outcome display; constrained Lumen context and numeric-reference validation.

**Preserve:** current report trust rules, review-first remediation, non-mutating public findings, and existing production behavior until replacement parity is proven.

**Gate:** every rendered value and every amount Lumen quotes resolves to a canonical metric or aggregate and its upstream evidence.

## Cross-repository CI matrix

- Supported Python versions and platforms.
- Package install and wheel build.
- Read-only-home help/version.
- Unit, property, contract, hostile-fixture, and golden tests.
- Consumer compatibility against current and previous supported CCAC minor versions.
- Documentation command execution.
- Non-root/read-only Docker smoke test.
- Nightly end-to-end illustrative pipeline using released package artifacts, not editable installs.

