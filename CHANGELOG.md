# Changelog

## 0.1.0 — 2026-08-04

- Add CCAC 1.0.0 draft schemas for tool results, pipeline manifests, trusted reports, and verified outcomes.
- Add structural JSON Schema validation and semantic trust validation.
- Add stable error codes for silent zero, verification, additivity, unattributed cost, mutating commands, SaaS activity, unsupported AI prices, overlap, reconciliation, references, and run integrity.
- Add `ccac validate` and `ccac validate-run` commands.
- Require trusted reports to preserve a quality summary and issue details for every included producer.
- Add valid reference artifacts, hostile cases, and 25 automated tests.
- Verify wheel build and installation in a clean virtual environment.
