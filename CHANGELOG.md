# Changelog

## 0.2.0 — unreleased

- Add explicit dispatch for preserved `ccac/1.0.0` and new `ccac/1.1.0` artifacts.
- Add typed Cloud, direct-AI, and SaaS boundaries and fail-closed technology-spend reconciliation.
- Use the existing typed reconciliation array as the sole source, with decimal/minor-unit arithmetic and run-level producer provenance.
- Keep producer calculations and released 1.0 pipeline artifacts unchanged.

## 0.1.0 — 2026-08-04

- Add CCAC 1.0.0 draft schemas for tool results, pipeline manifests, trusted reports, and verified outcomes.
- Add structural JSON Schema validation and semantic trust validation.
- Add stable error codes for silent zero, verification, additivity, unattributed cost, mutating commands, SaaS activity, unsupported AI prices, overlap, reconciliation, references, and run integrity.
- Add `ccac validate` and `ccac validate-run` commands.
- Require trusted reports to preserve a quality summary and issue details for every included producer.
- Add valid reference artifacts, hostile cases, and 25 imported automated tests. The standalone repository bootstrap adds one Python 3.10 compatibility test, for 26 collected tests total.
- Verify wheel build and installation in a clean virtual environment.
