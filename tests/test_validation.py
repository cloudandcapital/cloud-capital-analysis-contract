from __future__ import annotations

from copy import deepcopy

import pytest

from ccac.errors import ErrorCode
from ccac.validator import validate_document


def codes(document):
    return {issue.code for issue in validate_document(document)}


def test_valid_tool_result_passes(valid_tool_result):
    assert validate_document(valid_tool_result) == []


def test_valid_trusted_report_passes(valid_report):
    assert validate_document(valid_report) == []


def test_missing_required_field_fails_schema(valid_tool_result):
    del valid_tool_result["run_id"]
    assert ErrorCode.SCHEMA_INVALID in codes(valid_tool_result)


def test_dangling_evidence_reference_fails(valid_tool_result):
    valid_tool_result["metrics"][0]["evidence_ids"] = ["evidence.missing"]
    assert ErrorCode.DANGLING_REFERENCE in codes(valid_tool_result)


def test_verified_metric_requires_outcome_document(valid_tool_result):
    valid_tool_result["metrics"][0]["basis"] = "verified"
    assert ErrorCode.VERIFIED_REQUIRES_VERIFIED_OUTCOME_DOCUMENT in codes(valid_tool_result)


def test_mutating_review_step_fails(valid_tool_result, opportunity):
    opportunity["review"]["non_mutating_review_steps"] = ["aws ec2 terminate-instances --instance-ids i-example"]
    valid_tool_result["opportunities"] = [opportunity]
    assert ErrorCode.MUTATING_COMMAND_NOT_ALLOWED in codes(valid_tool_result)


def test_unattributed_cost_is_not_savings(valid_tool_result, opportunity):
    opportunity["scope"]["classification"] = "unattributed_cost"
    valid_tool_result["opportunities"] = [opportunity]
    assert ErrorCode.UNATTRIBUTED_COST_IS_NOT_SAVINGS in codes(valid_tool_result)


def test_parse_failure_cannot_become_valid_zero(valid_tool_result):
    valid_tool_result["quality"] = {"status": "partial", "issues": [{"code": "numeric.parse", "severity": "error", "message": "Could not parse amount", "source_id": "source.focus.aws", "field": "EffectiveCost", "row_count": 1}]}
    valid_tool_result["metrics"][0]["value"] = 0
    assert ErrorCode.PARSE_FAILURE_CANNOT_PRODUCE_VALID_ZERO in codes(valid_tool_result)


def test_unsupported_ai_price_is_unknown_not_zero(valid_tool_result):
    valid_tool_result["producer"] = {"name": "ai-cost-lens", "version": "1.0.0"}
    metric = valid_tool_result["metrics"][0]
    metric["value"] = 0
    metric["basis"] = "calculated"
    metric["formula"] = "tokens multiplied by price book rate"
    metric["dimensions"]["price_book_match"] = False
    assert ErrorCode.UNSUPPORTED_PRICE_MUST_BE_UNKNOWN in codes(valid_tool_result)


def test_missing_saas_activity_is_unknown_not_inactive(valid_tool_result):
    valid_tool_result["producer"] = {"name": "saas-cost-analyzer", "version": "1.0.0"}
    metric = valid_tool_result["metrics"][0]
    metric["dimensions"].update({"activity_evidence": False, "activity_status": "inactive"})
    assert ErrorCode.MISSING_ACTIVITY_MUST_BE_UNKNOWN in codes(valid_tool_result)


def test_complete_report_requires_every_producer(valid_report):
    valid_report["included_producers"] = valid_report["included_producers"][:-1]
    assert ErrorCode.COMPLETE_REPORT_MISSING_PRODUCER in codes(valid_report)


def test_producer_quality_must_cover_included_producers_exactly_once(valid_report):
    valid_report["producer_quality"] = valid_report["producer_quality"][:-1]
    assert ErrorCode.PRODUCER_MISMATCH in codes(valid_report)


def test_producer_quality_preserves_issues(valid_report):
    summary = valid_report["producer_quality"][-1]
    summary["quality"] = {
        "status": "partial",
        "issues": [{"code": "quality.saas.activity", "severity": "warning", "message": "Activity evidence is stale."}],
    }
    assert validate_document(valid_report) == []


def test_display_reference_must_resolve(valid_report):
    valid_report["display"]["headline_metric_ids"].append("metric.missing")
    assert ErrorCode.REPORT_DISPLAY_REFERENCE_MISSING in codes(valid_report)


def test_non_additive_metric_cannot_enter_total(valid_report):
    valid_report["metric_catalog"][0]["additivity"] = "non_additive"
    assert ErrorCode.NON_ADDITIVE_METRIC_INCLUDED_IN_TOTAL in codes(valid_report)


def test_exclusive_overlap_cannot_be_counted_twice(valid_report, opportunity):
    first = deepcopy(opportunity)
    second = deepcopy(opportunity)
    first["id"] = "opportunity.compute.rightsize"
    second["id"] = "opportunity.compute.commitment"
    for item in (first, second):
        item["overlap"] = {"disposition": "exclusive", "group_id": "overlap.compute.one", "reason": "Alternative treatments of the same compute scope."}
    valid_report["opportunity_catalog"] = [first, second]
    valid_report["opportunity_aggregates"] = [{
        "id": "aggregate.compute",
        "label": "Compute opportunities",
        "opportunity_ids": [first["id"], second["id"]],
        "excluded_opportunity_ids": [],
        "period": "monthly",
        "low": 20,
        "expected": 40,
        "high": 60,
        "currency": "USD",
        "inclusion_rule": "Invalid fixture deliberately includes both alternatives.",
    }]
    assert ErrorCode.EXCLUSIVE_OVERLAP_INCLUDED_MORE_THAN_ONCE in codes(valid_report)


@pytest.mark.parametrize("field,value", [("low", 19), ("expected", 39), ("high", 59)])
def test_aggregate_ranges_must_reconcile(valid_report, opportunity, field, value):
    valid_report["opportunity_catalog"] = [opportunity]
    aggregate = {
        "id": "aggregate.test",
        "label": "Test aggregate",
        "opportunity_ids": [opportunity["id"]],
        "excluded_opportunity_ids": [],
        "period": "monthly",
        "low": 10,
        "expected": 20,
        "high": 30,
        "currency": "USD",
        "inclusion_rule": "Include independent opportunity.",
    }
    aggregate[field] = value
    valid_report["opportunity_aggregates"] = [aggregate]
    assert ErrorCode.AGGREGATE_DOES_NOT_RECONCILE in codes(valid_report)
