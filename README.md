# Cloud & Capital Analysis Contract (CCAC)

CCAC is the versioned data contract and independent reference validator between Cloud & Capital analytical producers and trusted consumers. It defines artifact structure, identity, lineage, quality, additivity, overlap, reconciliation, and estimate-versus-outcome rules. It is not a billing connector or cost-calculation engine.

The current contract identity is `ccac/1.0.0`. The reference Python package is `cloudandcapital-ccac` 0.1.0 and uses JSON Schema 2020-12.

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

The contract string (currently `ccac/1.0.0`) versions artifact semantics. Breaking schema or semantic changes require a new contract major version and explicit version selection or migration behavior. Additive changes are versioned honestly and cannot silently reinterpret existing `ccac/1.0.0` documents. Python package versions describe validator releases and are separate from the contract identity.

This initial repository bootstrap preserves the audited `ccac/1.0.0` reference behavior. New accounting-boundary semantics will be proposed and reviewed separately; they are not part of this bootstrap.

## Repository map

- `schemas/`: versioned JSON Schemas
- `src/ccac/`: Python reference validator and CLI
- `fixtures/valid/`: accepted examples
- `fixtures/hostile/`: adversarial examples that must be rejected
- `tests/`: schema, semantic, CLI, and run-integrity tests
- `acceptance-suite.md`, `semantic-rules.md`, `calculation-ownership.md`: normative design material
- `docs/source-provenance.md`: audited import record

See [CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes and [SECURITY.md](SECURITY.md) for private vulnerability reporting.
