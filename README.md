# Cloud & Capital Analysis Contract (CCAC)

CCAC is the versioned data contract and independent reference validator between Cloud & Capital analytical producers and trusted consumers. It defines artifact structure, identity, lineage, quality, additivity, overlap, reconciliation, and estimate-versus-outcome rules. It is not a billing connector or cost-calculation engine.

The reference package is `cloudandcapital-ccac` 0.2.0 and uses JSON Schema 2020-12. It dispatches explicitly between preserved `ccac/1.0.0` behavior and the accounting-boundary-capable `ccac/1.1.0`; unsupported versions fail closed.

## Accounting boundaries in 1.1

CCAC 1.1 classifies three mutually exclusive technology-spend scopes by billing channel:

- `cloud`, owned by FinOps Lite, includes native AI services billed by AWS, Azure, or GCP and excludes direct AI-vendor billing.
- `direct_ai`, owned by AI Cost Lens, includes direct AI-vendor usage or invoices and excludes provider-billed AI.
- `saas`, owned by SaaS Cost Analyzer, includes SaaS invoices or entitlements and excludes vendors classified as direct AI.

A scope metric declares owner, source channel, cost basis, inclusion and exclusion rules, coverage, overlap disposition, component treatments, total eligibility, and reason. Existing metric period, currency, additivity, evidence, formula inputs, and quality remain authoritative. Allocations and components may describe a scope but cannot be added as new spend.

An all-in total requires exactly one eligible metric per scope, identical periods/timezones, currency, cost basis, and declared currency minor unit. The existing `reconciliation` array is the sole reconciliation source of truth: exactly one entry discriminated by `reconciliation_type: technology_spend_total` is required when the total is advertised. Values, differences, and a tolerance no larger than the common minor unit are compared with decimal arithmetic. Partial, unknown, invalid, non-additive, modeled, estimated, forecast, unresolved, or evidence-free inputs fail closed. Partial reports may show scopes individually but cannot advertise an all-in total. Automatic FX conversion is out of scope.

Periods are start-inclusive and end-exclusive. Omitted timezones normalize to the schema default, UTC. A scope metric must match its producer result period; reconciled inputs and output must also match the trusted-report period.

Standalone report validation proves the declarations and arithmetic. Complete producer provenance is established only by run-directory validation, which requires each reported canonical scope metric to match exactly one metric from its declared owner's tool-result artifact on every financially meaningful field.

This capability enables a future scope breakdown and donut. It does not connect Cloud Cost Guard and is not a claim of GAAP compliance, audited accounting, official FOCUS conformance, or complete enterprise billing coverage.

## Current pipeline compatibility

This bootstrap preserves the previously audited validation behavior for:

- FinOps Lite 0.3.0
- FinOps Watchdog 0.4.0
- Recovery Economics 0.2.1
- AI Cost Lens 0.2.0
- SaaS Cost Analyzer 0.2.0
- Tech Spend Command Center 0.2.1

The released illustrative pipeline produces five `tool_result` artifacts, one `pipeline_manifest`, and one `trusted_report`. CCAC validates their schemas and cross-document semantics without recalculating producer-owned financial values.

Cloud Cost Guard integration remains planned. This repository does not claim PyPI publication, production support, official FOCUS conformance, live dashboard integration, or access to provider systems. Its illustrative fixtures contain no customer accounts, credentials, or production resources.

## Development installation

Python 3.10 or newer is required. With [uv](https://docs.astral.sh/uv/):

```bash
uv sync --extra dev
```

Or with a disposable virtual environment and pip:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
```

## Validate artifacts

```bash
uv run ccac --version
uv run ccac validate fixtures/valid/minimal-finops-lite-result.json
uv run ccac validate-run path/to/run-directory
```

An invalid artifact or run prints structured issues and exits nonzero.

## Test and build

```bash
uv run pytest
uv build
```

The wheel contains the validator and all five contract schemas. CI exercises the supported Python matrix, valid fixtures, hostile-fixture rejection, package build, clean installation, CLI smoke tests, and JSON/schema parsing.

## Contract layers

1. Analytical producers own their calculations and emit CCAC `tool_result` documents.
2. A `pipeline_manifest` locks producer identity, run identity, artifact paths, versions, and hashes.
3. Tech Spend Command Center validates and aggregates canonical references into a `trusted_report` without inventing totals or savings.
4. Trusted consumers use canonical IDs and provenance rather than reinterpreting display labels.
5. A later `verified_outcome` is distinct from an estimate and requires its own evidence.

Core rules include fail-closed missing values, explicit basis and additivity, evidence-backed displayed metrics, overlap-aware opportunities, immutable run identity, and preservation of producer quality warnings.

## Versioning

The contract string versions artifact semantics. `ccac/1.0.0` remains supported without reinterpretation; `ccac/1.1.0` adds opt-in accounting-boundary fields and rules. Breaking changes require a new major version and explicit selection or migration. Python package versions describe validator releases and remain separate from contract identity.

The 1.1 capability is contract infrastructure only. Producers do not emit these scope metrics yet.

## Repository map

- `schemas/`: versioned JSON Schemas
- `src/ccac/`: Python reference validator and CLI
- `fixtures/valid/`: accepted examples
- `fixtures/hostile/`: adversarial examples that must be rejected
- `tests/`: schema, semantic, CLI, and run-integrity tests
- `acceptance-suite.md`, `semantic-rules.md`, `calculation-ownership.md`: normative design material
- `docs/source-provenance.md`: audited import record

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes and [SECURITY.md](SECURITY.md) for private vulnerability reporting.
