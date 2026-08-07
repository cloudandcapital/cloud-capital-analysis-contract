# Bootstrap source provenance

Audit date: 2026-08-07  
Neutral source identifier: `cloud-capital-v0-2.2-remaining-tools/reference/source`  
Contract identity: `ccac/1.0.0`  
Reference package: `cloudandcapital-ccac` 0.1.0

This repository was bootstrapped from the standalone reference source used to independently validate the released six-tool illustrative pipeline. The retained pre-import inventory contains 38 source, schema, fixture, test, package, and design files. `docs/source-preimport-sha256.txt` and `docs/source-postimport-sha256.txt` record their before-and-after hashes.

The imported validator behavior and financial semantics are unchanged. All authoritative files except `README.md`, `LICENSE`, `src/ccac/errors.py`, and `tests/test_validation.py` retain the same path and bytes. `README.md` was rewritten only to describe the standalone public repository accurately; `LICENSE` had one surplus terminal blank line removed so repository whitespace checks pass. A Python 3.10 fallback for `enum.StrEnum` and its behavior test were added because the audited package declares Python 3.10 support while the standard-library class begins in Python 3.11. Their original hashes remain in the pre-import manifest. The initial GitHub-generated README and license were replaced by the audited source files. Added bootstrap-only material is otherwise limited to `.gitignore`, GitHub Actions CI, contributing guidance, security guidance, and this provenance record.

Compatibility validated before import:

- FinOps Lite 0.3.0
- FinOps Watchdog 0.4.0
- Recovery Economics 0.2.1
- AI Cost Lens 0.2.0
- SaaS Cost Analyzer 0.2.0
- Tech Spend Command Center 0.2.1

The source previously passed independent validation of five producer artifacts, `manifest.json`, and `report.json`. This bootstrap adds no accounting-boundary semantics, schema fields, semantic rules, releases, or dashboard integration.
