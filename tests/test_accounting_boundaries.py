from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ccac.errors import ErrorCode
from ccac.validator import validate_document


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "valid" / "1.1.0"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def codes(document: dict) -> set[ErrorCode]:
    return {issue.code for issue in validate_document(document)}


@pytest.mark.parametrize(
    "name",
    ["cloud-scope.json", "direct_ai-scope.json", "saas-scope.json", "partial-scope.json", "technology-spend-report.json"],
)
def test_valid_accounting_boundary_fixtures(name):
    assert validate_document(load(name)) == []


def test_provider_billed_ai_cannot_enter_direct_ai():
    document = load("direct_ai-scope.json")
    document["metrics"][0]["accounting_boundary"]["cross_scope_treatments"]["provider_billed_ai"] = "included"
    assert ErrorCode.ACCOUNTING_BOUNDARY_POLICY_INVALID in codes(document)


def test_direct_ai_vendor_cannot_enter_saas():
    document = load("saas-scope.json")
    document["metrics"][0]["accounting_boundary"]["cross_scope_treatments"]["direct_ai_vendor"] = "included"
    assert ErrorCode.ACCOUNTING_BOUNDARY_POLICY_INVALID in codes(document)


def test_wrong_producer_cannot_own_scope():
    document = load("cloud-scope.json")
    document["producer"] = {"name": "finops-watchdog", "version": "0.0.0"}
    assert ErrorCode.ACCOUNTING_BOUNDARY_OWNER_INVALID in codes(document)


def test_duplicate_canonical_scope_fails():
    document = load("technology-spend-report.json")
    duplicate = deepcopy(document["metric_catalog"][0])
    duplicate["id"] = "metric.tech-spend.scope.cloud.duplicate"
    document["metric_catalog"].append(duplicate)
    assert ErrorCode.CANONICAL_SCOPE_DUPLICATE in codes(document)


def test_missing_scope_in_claimed_total_fails():
    document = load("technology-spend-report.json")
    ids = ["metric.tech-spend.scope.cloud", "metric.tech-spend.scope.direct_ai", "metric.tech-spend.total"]
    document["technology_spend_reconciliation"]["input_metric_ids"] = ids
    document["metric_catalog"][-1]["input_metric_ids"] = ids
    assert ErrorCode.CANONICAL_SCOPE_MISSING in codes(document)


@pytest.mark.parametrize("field,value", [("currency", "EUR"), ("period", {"start": "2026-07-02", "end": "2026-08-01", "timezone": "UTC"})])
def test_currency_or_period_mismatch_fails(field, value):
    document = load("technology-spend-report.json")
    document["metric_catalog"][1][field] = value
    assert ErrorCode.CANONICAL_SCOPE_MISMATCH in codes(document)


def test_unresolved_overlap_cannot_be_total_eligible():
    document = load("cloud-scope.json")
    document["metrics"][0]["accounting_boundary"]["overlap"]["disposition"] = "unresolved"
    assert ErrorCode.ACCOUNTING_BOUNDARY_INELIGIBLE in codes(document)


def test_partial_scope_cannot_enter_total():
    document = load("technology-spend-report.json")
    partial = load("partial-scope.json")["metrics"][0]
    document["metric_catalog"][1] = partial
    assert ErrorCode.ACCOUNTING_BOUNDARY_INELIGIBLE in codes(document)


@pytest.mark.parametrize("field,value", [("additivity", "non_additive"), ("basis", "modeled"), ("basis", "estimated"), ("basis", "forecast")])
def test_non_cost_or_non_additive_scope_cannot_enter_total(field, value):
    document = load("technology-spend-report.json")
    document["metric_catalog"][0][field] = value
    if field == "basis":
        document["metric_catalog"][0]["formula"] = "unsupported value for observed spend total"
    assert ErrorCode.ACCOUNTING_BOUNDARY_INELIGIBLE in codes(document)


@pytest.mark.parametrize("field", ["inclusion_rules", "exclusion_rules", "component_treatments"])
def test_missing_boundary_declaration_fails_schema(field):
    document = load("cloud-scope.json")
    del document["metrics"][0]["accounting_boundary"][field]
    assert ErrorCode.ACCOUNTING_BOUNDARY_DECLARATION_MISSING in codes(document)


def test_missing_evidence_fails_schema():
    document = load("cloud-scope.json")
    document["metrics"][0]["evidence_ids"] = []
    assert ErrorCode.ACCOUNTING_BOUNDARY_EVIDENCE_MISSING in codes(document)


def test_combined_total_must_reconcile():
    document = load("technology-spend-report.json")
    document["metric_catalog"][-1]["value"] = 1499
    assert ErrorCode.TECHNOLOGY_SPEND_RECONCILIATION_INVALID in codes(document)


def test_partial_report_cannot_advertise_all_in_total():
    document = load("technology-spend-report.json")
    document["status"] = "partial"
    document["omitted_producers"] = [{"name": "finops-watchdog", "reason": "Not supplied."}]
    assert ErrorCode.TECHNOLOGY_SPEND_RECONCILIATION_INVALID in codes(document)


def test_unsupported_contract_version_fails_closed():
    document = load("cloud-scope.json")
    document["contract"] = "ccac/2.0.0"
    assert codes(document) == {ErrorCode.UNSUPPORTED_CONTRACT}


def test_legacy_document_is_not_reinterpreted_as_1_1():
    document = json.loads((ROOT / "fixtures" / "valid" / "minimal-finops-lite-result.json").read_text())
    document["metrics"][0]["accounting_boundary"] = load("cloud-scope.json")["metrics"][0]["accounting_boundary"]
    assert ErrorCode.SCHEMA_INVALID in codes(document)


def test_total_requires_complete_canonical_input_ids():
    document = load("technology-spend-report.json")
    document["metric_catalog"][-1]["input_metric_ids"] = []
    assert ErrorCode.TECHNOLOGY_SPEND_RECONCILIATION_INVALID in codes(document)
