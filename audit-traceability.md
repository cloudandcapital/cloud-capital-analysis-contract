# Audit-to-Contract Traceability

| Proven audit failure or trust risk | Contract/design control | Acceptance coverage |
|---|---|---|
| FinOps Lite real output became `$0` in Command Center | Required metric value/basis/quality; exact schema; no parser defaults | S-003, F-003, D-009; `silent-zero.json` |
| Recovery nested total became `$0` | Exact producer contract and required references | S-003, D-009; `silent-zero.json` |
| Watchdog anomaly became `Unknown` with blank message | Required finding title, type, metrics, evidence, and timestamps | S-002, D-001, D-009 |
| Command Center invented 15% SaaS savings | Exclusive SaaS calculation ownership; Command Center originates no domain amount | D-008, D-010; `estimate-labeled-verified.json` |
| Missing SaaS usage was treated as unused | Explicit unknown state and evidence requirement | D-007; `missing-saas-activity-as-unused.json` |
| AI numeric parse errors became zero | Unknown/null rule and price/data quality coverage | F-003, D-005, D-006; `unsupported-ai-model-zero.json` |
| Unsupported AI model could look free | Unsupported price must be unknown | D-006; `unsupported-ai-model-zero.json` |
| Kubernetes could overlap cloud spend | Metric additivity classification | F-005; `double-counted-kubernetes.json` |
| Untagged spend could be mistaken for savings | `unattributed_cost` classification; opportunity prohibition | F-006; `untagged-as-savings.json` |
| Overlapping opportunities could be added twice | Overlap dispositions/groups and aggregate inclusion rules | T-001–T-003; `overlap-included-twice.json` |
| Estimates could be described as savings | Basis ladder and separate verified-outcome document | F-008, F-009; `estimate-labeled-verified.json` |
| Public findings contained mutating commands in legacy backend | Non-mutating review steps; semantic command blocklist | T-004; `mutating-public-command.json` |
| Public report was manually authored | Immutable run manifest, hashes, producer catalog, display references | S-001, S-006, S-007, T-005 |
| README commands differed from installed CLIs | CI executes documentation commands | Fresh-install acceptance 1–8 |
| Help/version wrote to home | Read-only-home smoke test | Fresh-install acceptance 2 |
| Watchdog README algorithm differed from code | Published evaluation fixtures and algorithm identity gate | D-001, D-002; Watchdog implementation gate |
| Recovery claims exceeded its formula | Component reconciliation, scenario assumptions, restore evidence | D-003, D-004 |
| Partial/missing producers could look complete | Required producer set and explicit partial semantics | T-007, T-008 |
| Lumen could invent or combine numbers | Display catalog and numeric-reference validation | T-005, T-009 |

All critical cross-tool audit failures have at least one preventive contract control and one detection test. Formula-quality improvements are additionally gated in each producer's implementation specification.
