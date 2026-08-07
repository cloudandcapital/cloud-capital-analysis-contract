# Contributing

CCAC changes can alter trust and financial interpretation across multiple repositories. Keep pull requests focused, explain compatibility impact, and add semantic tests for both accepted and rejected behavior.

Before submitting a change:

1. State whether it changes the contract, validator package, documentation, or packaging only.
2. Apply semantic versioning to contract changes and never reinterpret an existing contract identity silently.
3. Add positive and hostile fixtures for new financial semantics.
4. Run `uv run pytest`, `uv build`, JSON/schema parsing, and `git diff --check`.
5. Do not include credentials, customer data, live billing exports, or mutating remediation commands.

Calculation ownership belongs to producers. The reference validator should validate declared meaning and lineage rather than reproduce financial calculations.
