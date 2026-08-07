# Calculation Ownership

## Canonical technology-spend scopes

| Scope | Producer owner | Billing channel | Required exclusion |
|---|---|---|---|
| Cloud | FinOps Lite | Cloud-provider billing | Direct AI-vendor invoices |
| Direct AI | AI Cost Lens | Direct AI-vendor usage or invoices | Provider-billed native AI |
| SaaS | SaaS Cost Analyzer | SaaS invoices or entitlements | Vendors classified as direct AI |

Tech Spend Command Center may reconcile and publish the combined total but may not originate or reinterpret the three amounts. Run-directory validation proves this by matching each reported scope to exactly one owner-produced metric across its complete financial representation. FinOps Watchdog and Recovery Economics may not originate canonical scope totals. Kubernetes is an allocation of Cloud and remains non-additive at this boundary.

## Ownership rule

The canonical owner is the only component allowed to originate that calculation. Consumers may filter, group, display, or reconcile owned metrics but may not recompute them with different formulas. A derived report metric is allowed only when its formula is declared and references canonical input metric IDs.

| Domain calculation | Canonical owner | Consumers | Explicit exclusions |
|---|---|---|---|
| Billing row normalization, billed/effective/list/contracted cost | FinOps Lite | All | Command Center and Cloud Cost Guard do not reinterpret provider rows. |
| Credits, refunds, discounts, amortization, currency basis | FinOps Lite | All | Missing amounts do not become zero. No automatic FX conversion in 1.0. |
| Allocation coverage, unattributed cost, shared-cost allocation | FinOps Lite | Watchdog, Command Center | Untagged spend is not savings. |
| Business unit cost and cost-per-unit using supplied unit metrics | FinOps Lite | Watchdog, Command Center | Unit counts are evidence-bearing inputs, not inferred by Command Center. |
| Cost period variance | FinOps Lite | Watchdog, Command Center | Command Center may display it, not reconstruct prior cost from a percentage. |
| Anomaly baseline, expected range, anomaly impact, contributors | FinOps Watchdog | Command Center | FinOps Lite signals are data-quality/concentration signals, not anomalies. |
| Resilience scenario cost, RTO/RPO coverage, resilience gaps | Recovery Economics | Command Center | A modeled resilience alternative is not generic cloud savings. |
| AI request/session/model cost and cost per outcome | AI Cost Lens | Watchdog, Command Center | Vendor-reported and price-book-estimated costs remain distinguishable. |
| AI token classification and price-book application | AI Cost Lens | Command Center | Unsupported model price is unknown, not zero. |
| SaaS entitlement, assignment, activity state, renewal exposure | SaaS Cost Analyzer | Command Center | Missing activity is unknown, not unused. |
| SaaS reclaim estimate and later realized SaaS outcome evidence | SaaS Cost Analyzer / verified outcome event | Command Center | Command Center cannot apply a blanket percentage. |
| Producer compatibility, inclusion/exclusion, reconciliation | Tech Spend Command Center | Cloud Cost Guard, Lumen | Aggregator cannot repair or guess malformed upstream documents. |
| Producer quality summaries and issue preservation | Tech Spend Command Center | Cloud Cost Guard, Lumen | Included producer warnings remain visible in the trusted report; `complete` means all producers are present, not that every producer is warning-free. |
| Opportunity overlap resolution and aggregates | Tech Spend Command Center | Cloud Cost Guard, Lumen | Overlapping items cannot both enter the same aggregate. |
| Dashboard formatting, filtering, drill-through | Cloud Cost Guard | User | Dashboard cannot originate financial values. |
| Natural-language explanation | Lumen | User | Lumen may quote only report metrics/aggregates and must preserve basis labels. |
| Operational approval, change, rollback, verification | External reviewed workflow | Verified outcome ingestion | No public pipeline component executes remediation. |

## Additivity classes

- `additive`: may be summed when currency, period, grain, and scope are compatible and scopes do not overlap.
- `non_additive`: an allocated or alternate view of another cost pool; displayed but excluded from parent totals. Kubernetes allocation is the first required example.
- `semi_additive`: may aggregate across dimensions but not blindly across time, such as seats or end-of-period inventory.
- `ratio`: never summed; numerator and denominator must be retained.

## Opportunity ownership and overlap

Each opportunity has exactly one `producer`. Cross-tool references use `related_opportunity_ids`; they do not clone the amount.

Overlap dispositions:

- `independent`: scopes are proven disjoint.
- `exclusive`: alternatives address the same economic scope; at most one may be included.
- `nested`: one opportunity's scope contains another; the aggregate must choose a documented inclusion rule.
- `potential`: overlap is unresolved; excluded from additive aggregates by default.
- `none_known`: no overlap found after declared checks; weaker than proven independence.

Command Center owns aggregate inclusion. Producers own opportunity evidence and estimate math.

## Basis ladder

| Basis | Meaning | Can become verified automatically? |
|---|---|---|
| `observed` | Directly reported by a source system/export | No |
| `calculated` | Deterministic formula over observed inputs | No |
| `allocated` | Assigned through a declared allocation rule | No |
| `estimated` | Scenario, forecast, recommendation, or modeled amount | No |
| `verified` | Confirmed post-change against a declared baseline and evidence window | Already verified; requires a separate verified outcome document |
| `unknown` | Not available or not supportably calculable | No |
