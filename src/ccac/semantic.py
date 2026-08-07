from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any, Iterable

from .errors import ErrorCode, ValidationIssue


MUTATING_COMMAND = re.compile(
    r"\b(delete|terminate|release|stop-instances|start-instances|resize|update|create|patch|modify-instance|remove|destroy)\b",
    re.IGNORECASE,
)
REQUIRED_ANALYTICAL_PRODUCERS = {
    "finops-lite",
    "finops-watchdog",
    "recovery-economics",
    "ai-cost-lens",
    "saas-cost-analyzer",
}
SCOPE_OWNERS = {
    "cloud": "finops-lite",
    "direct_ai": "ai-cost-lens",
    "saas": "saas-cost-analyzer",
}
SCOPE_CHANNELS = {
    "cloud": "cloud_provider_billing",
    "direct_ai": "direct_ai_vendor",
    "saas": "saas_invoice_or_entitlement",
}


def _issue(code: ErrorCode, message: str, path: str, detail: Any | None = None) -> ValidationIssue:
    return ValidationIssue(code, message, path, detail)


def _duplicates(values: Iterable[str]) -> set[str]:
    counts = Counter(values)
    return {value for value, count in counts.items() if count > 1}


def _catalog(document: dict[str, Any], key: str) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in document.get(key, []) if isinstance(item, dict) and isinstance(item.get("id"), str)}


def _check_unique(document: dict[str, Any], key: str, issues: list[ValidationIssue]) -> None:
    ids = [item.get("id") for item in document.get(key, []) if isinstance(item, dict) and item.get("id")]
    for duplicate in sorted(_duplicates(ids)):
        issues.append(_issue(ErrorCode.DUPLICATE_ID, f"Duplicate ID {duplicate!r} in {key}", f"$.{key}"))


def _check_refs(refs: Iterable[str], available: set[str], path: str, issues: list[ValidationIssue]) -> None:
    for ref in refs:
        if ref not in available:
            issues.append(_issue(ErrorCode.DANGLING_REFERENCE, f"Reference {ref!r} does not resolve", path))


def _validate_metrics(metrics: list[dict[str, Any]], evidence_ids: set[str], issues: list[ValidationIssue]) -> None:
    metric_ids = {metric.get("id") for metric in metrics}
    for index, metric in enumerate(metrics):
        path = f"$.metrics[{index}]"
        value = metric.get("value")
        basis = metric.get("basis")
        if value is None and (basis != "unknown" or not metric.get("unknown_reason")):
            issues.append(_issue(ErrorCode.UNKNOWN_VALUE_REQUIRED, "Null metric requires basis=unknown and unknown_reason", path))
        if basis in {"calculated", "allocated", "modeled", "estimated", "forecast"} and not metric.get("formula"):
            issues.append(_issue(ErrorCode.FORMULA_REQUIRED, f"{basis} metric requires a formula", path))
        if basis == "verified":
            issues.append(_issue(ErrorCode.VERIFIED_REQUIRES_VERIFIED_OUTCOME_DOCUMENT, "Verified values are allowed only in verified_outcome documents", path))
        _check_refs(metric.get("evidence_ids", []), evidence_ids, f"{path}.evidence_ids", issues)
        _check_refs(metric.get("input_metric_ids", []), metric_ids, f"{path}.input_metric_ids", issues)


def _validate_boundary(metric: dict[str, Any], path: str, issues: list[ValidationIssue], producer: str | None = None) -> None:
    boundary = metric.get("accounting_boundary")
    if not isinstance(boundary, dict):
        return
    scope = boundary.get("scope")
    owner = SCOPE_OWNERS.get(scope)
    if owner is None or boundary.get("canonical_owner") != owner or (producer is not None and producer != owner):
        issues.append(_issue(ErrorCode.ACCOUNTING_BOUNDARY_OWNER_INVALID, f"Canonical scope {scope!r} must be owned by {owner!r}", f"{path}.accounting_boundary.canonical_owner"))
    if boundary.get("source_channel") != SCOPE_CHANNELS.get(scope):
        issues.append(_issue(ErrorCode.ACCOUNTING_BOUNDARY_POLICY_INVALID, f"Canonical scope {scope!r} has the wrong billing channel", f"{path}.accounting_boundary.source_channel"))
    cross = boundary.get("cross_scope_treatments", {})
    policy_ok = (
        scope == "cloud" and cross.get("provider_billed_ai") == "included" and cross.get("direct_ai_vendor") == "excluded"
    ) or (
        scope == "direct_ai" and cross.get("provider_billed_ai") == "excluded" and cross.get("direct_ai_vendor") == "included"
    ) or (
        scope == "saas" and cross.get("provider_billed_ai") in {"excluded", "not_applicable"} and cross.get("direct_ai_vendor") == "excluded"
    )
    if not policy_ok:
        issues.append(_issue(ErrorCode.ACCOUNTING_BOUNDARY_POLICY_INVALID, f"Canonical scope {scope!r} violates the cross-scope billing policy", f"{path}.accounting_boundary.cross_scope_treatments"))
    relationship = boundary.get("relationship")
    if relationship != "canonical_scope_spend" and boundary.get("total_eligible"):
        issues.append(_issue(ErrorCode.ACCOUNTING_BOUNDARY_INELIGIBLE, "Allocations and components cannot enter the all-in total", f"{path}.accounting_boundary.total_eligible"))
    if boundary.get("total_eligible"):
        eligible = (
            relationship == "canonical_scope_spend"
            and metric.get("value") is not None
            and metric.get("unit") == "currency"
            and metric.get("currency") is not None
            and metric.get("additivity") == "additive"
            and metric.get("basis") in {"observed", "calculated"}
            and metric.get("quality_status") == "valid"
            and boundary.get("coverage") == "complete"
            and boundary.get("overlap", {}).get("disposition") in {"resolved", "excluded"}
            and bool(metric.get("evidence_ids"))
        )
        if not eligible:
            issues.append(_issue(ErrorCode.ACCOUNTING_BOUNDARY_INELIGIBLE, f"Canonical scope {scope!r} does not satisfy all-in total eligibility", f"{path}.accounting_boundary"))


def validate_tool_result(document: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for key in ("inputs", "metrics", "findings", "opportunities", "evidence"):
        _check_unique(document, key, issues)

    source_ids = {item.get("id") for item in document.get("inputs", [])}
    evidence = _catalog(document, "evidence")
    metrics = _catalog(document, "metrics")
    findings = _catalog(document, "findings")
    opportunities = _catalog(document, "opportunities")

    for index, item in enumerate(evidence.values()):
        _check_refs(item.get("source_ids", []), source_ids, f"$.evidence[{index}].source_ids", issues)
    _validate_metrics(list(metrics.values()), set(evidence), issues)
    if document.get("contract") == "ccac/1.1.0":
        for index, metric in enumerate(metrics.values()):
            _validate_boundary(metric, f"$.metrics[{index}]", issues, document.get("producer", {}).get("name"))

    for index, finding in enumerate(findings.values()):
        _check_refs(finding.get("metric_ids", []), set(metrics), f"$.findings[{index}].metric_ids", issues)
        _check_refs(finding.get("evidence_ids", []), set(evidence), f"$.findings[{index}].evidence_ids", issues)

    result_producer = document.get("producer", {}).get("name")
    for index, opportunity in enumerate(opportunities.values()):
        path = f"$.opportunities[{index}]"
        if opportunity.get("producer", {}).get("name") != result_producer:
            issues.append(_issue(ErrorCode.PRODUCER_MISMATCH, "Opportunity producer must match result producer", f"{path}.producer.name"))
        estimate = opportunity.get("estimate", {})
        low, expected, high = estimate.get("low"), estimate.get("expected"), estimate.get("high")
        if all(isinstance(value, (int, float)) for value in (low, expected, high)) and not low <= expected <= high:
            issues.append(_issue(ErrorCode.INVALID_ESTIMATE_RANGE, "Estimate must satisfy low <= expected <= high", f"{path}.estimate"))
        _check_refs(opportunity.get("evidence_ids", []), set(evidence), f"{path}.evidence_ids", issues)
        _check_refs(opportunity.get("related_finding_ids", []), set(findings), f"{path}.related_finding_ids", issues)
        _check_refs(opportunity.get("related_opportunity_ids", []), set(opportunities), f"{path}.related_opportunity_ids", issues)
        for step_index, step in enumerate(opportunity.get("review", {}).get("non_mutating_review_steps", [])):
            if MUTATING_COMMAND.search(step):
                issues.append(_issue(ErrorCode.MUTATING_COMMAND_NOT_ALLOWED, "Review step appears to contain a mutating command", f"{path}.review.non_mutating_review_steps[{step_index}]"))
        scope = opportunity.get("scope", {})
        if scope.get("classification") == "unattributed_cost" or opportunity.get("opportunity_type") == "unattributed_cost":
            issues.append(_issue(ErrorCode.UNATTRIBUTED_COST_IS_NOT_SAVINGS, "Unattributed cost cannot be a savings opportunity", path))

    quality_codes = {item.get("code") for item in document.get("quality", {}).get("issues", [])}
    if any(code and ("parse" in code or "numeric" in code) for code in quality_codes):
        for metric in metrics.values():
            if metric.get("value") == 0 and metric.get("quality_status") == "valid":
                issues.append(_issue(ErrorCode.PARSE_FAILURE_CANNOT_PRODUCE_VALID_ZERO, "A parse failure cannot produce a valid zero metric", f"$.metrics[{metric.get('id')}]"))

    if result_producer == "ai-cost-lens":
        for metric in metrics.values():
            dimensions = metric.get("dimensions", {})
            if dimensions.get("price_book_match") is False and metric.get("value") == 0 and metric.get("basis") == "calculated":
                issues.append(_issue(ErrorCode.UNSUPPORTED_PRICE_MUST_BE_UNKNOWN, "Unsupported model price must produce an unknown cost", f"$.metrics[{metric.get('id')}]"))
    if result_producer == "saas-cost-analyzer":
        for metric in metrics.values():
            dimensions = metric.get("dimensions", {})
            if dimensions.get("activity_evidence") is False and dimensions.get("activity_status") == "inactive":
                issues.append(_issue(ErrorCode.MISSING_ACTIVITY_MUST_BE_UNKNOWN, "Missing activity evidence must be classified as unknown", f"$.metrics[{metric.get('id')}]"))
    return issues


def validate_trusted_report(document: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for key in ("metric_catalog", "finding_catalog", "opportunity_catalog", "opportunity_aggregates", "reconciliation"):
        _check_unique(document, key, issues)
    metrics = _catalog(document, "metric_catalog")
    findings = _catalog(document, "finding_catalog")
    opportunities = _catalog(document, "opportunity_catalog")
    aggregates = _catalog(document, "opportunity_aggregates")

    if document.get("status") == "complete":
        included = {item.get("name") for item in document.get("included_producers", [])}
        missing = REQUIRED_ANALYTICAL_PRODUCERS - included
        if missing:
            issues.append(_issue(ErrorCode.COMPLETE_REPORT_MISSING_PRODUCER, f"Complete report is missing producers: {sorted(missing)}", "$.included_producers"))
    included = {item.get("name") for item in document.get("included_producers", [])}
    quality_names = [item.get("producer", {}).get("name") for item in document.get("producer_quality", [])]
    if len(quality_names) != len(set(quality_names)) or set(quality_names) != included:
        issues.append(_issue(ErrorCode.PRODUCER_MISMATCH, "Producer quality summaries must match included producers exactly once", "$.producer_quality"))
    if document.get("mode") == "illustrative" and not any("illustrative" in text.lower() for text in document.get("display", {}).get("disclosures", [])):
        issues.append(_issue(ErrorCode.ILLUSTRATIVE_DISCLOSURE_REQUIRED, "Illustrative report requires a visible disclosure", "$.display.disclosures"))

    display = document.get("display", {})
    metric_refs = list(display.get("headline_metric_ids", []))
    for refs in display.get("section_metric_ids", {}).values():
        metric_refs.extend(refs)
    for ref, available, path in (
        (metric_refs, set(metrics), "$.display"),
        (display.get("finding_ids", []), set(findings), "$.display.finding_ids"),
        (display.get("opportunity_aggregate_ids", []), set(aggregates), "$.display.opportunity_aggregate_ids"),
    ):
        for item in ref:
            if item not in available:
                issues.append(_issue(ErrorCode.REPORT_DISPLAY_REFERENCE_MISSING, f"Display reference {item!r} does not resolve", path))

    for index, aggregate in enumerate(aggregates.values()):
        path = f"$.opportunity_aggregates[{index}]"
        selected = [opportunities.get(item) for item in aggregate.get("opportunity_ids", [])]
        _check_refs(aggregate.get("opportunity_ids", []), set(opportunities), f"{path}.opportunity_ids", issues)
        groups: dict[str, list[str]] = defaultdict(list)
        for opportunity in filter(None, selected):
            overlap = opportunity.get("overlap", {})
            if overlap.get("disposition") == "exclusive" and overlap.get("group_id"):
                groups[overlap["group_id"]].append(opportunity["id"])
        for group_id, ids in groups.items():
            if len(ids) > 1:
                issues.append(_issue(ErrorCode.EXCLUSIVE_OVERLAP_INCLUDED_MORE_THAN_ONCE, f"Exclusive overlap group {group_id!r} includes {ids}", path))
        for field in ("low", "expected", "high"):
            total = round(sum(item["estimate"][field] for item in filter(None, selected)), 2)
            if round(aggregate.get(field, 0), 2) != total:
                issues.append(_issue(ErrorCode.AGGREGATE_DOES_NOT_RECONCILE, f"Aggregate {field}={aggregate.get(field)} but included opportunities sum to {total}", f"{path}.{field}"))

    for index, reconciliation in enumerate(document.get("reconciliation", [])):
        _check_refs(reconciliation.get("input_metric_ids", []), set(metrics), f"$.reconciliation[{index}].input_metric_ids", issues)
        _check_refs([reconciliation.get("output_metric_id")], set(metrics), f"$.reconciliation[{index}].output_metric_id", issues)
        if reconciliation.get("status") != "passed" or abs(reconciliation.get("difference", 0)) > reconciliation.get("tolerance", 0):
            issues.append(_issue(ErrorCode.RECONCILIATION_FAILED, "Trusted report contains a failed reconciliation", f"$.reconciliation[{index}]"))
        input_metrics = [metrics.get(item) for item in reconciliation.get("input_metric_ids", [])]
        if any(item and item.get("additivity") == "non_additive" for item in input_metrics):
            issues.append(_issue(ErrorCode.NON_ADDITIVE_METRIC_INCLUDED_IN_TOTAL, "Reconciliation includes a non-additive metric", f"$.reconciliation[{index}].input_metric_ids"))
    if document.get("contract") == "ccac/1.1.0":
        _validate_technology_spend(document, metrics, issues)
    return issues


def _validate_technology_spend(document: dict[str, Any], metrics: dict[str, dict[str, Any]], issues: list[ValidationIssue]) -> None:
    boundary_metrics = [metric for metric in metrics.values() if isinstance(metric.get("accounting_boundary"), dict)]
    for index, metric in enumerate(boundary_metrics):
        _validate_boundary(metric, f"$.metric_catalog[{index}]", issues)
    canonical = [metric for metric in boundary_metrics if metric["accounting_boundary"].get("relationship") == "canonical_scope_spend"]
    scopes = [metric["accounting_boundary"].get("scope") for metric in canonical]
    for duplicate in sorted(_duplicates(scopes)):
        issues.append(_issue(ErrorCode.CANONICAL_SCOPE_DUPLICATE, f"Duplicate canonical scope {duplicate!r}", "$.metric_catalog"))

    reconciliation = document.get("technology_spend_reconciliation")
    display = document.get("display", {})
    displayed = set(display.get("headline_metric_ids", []))
    for refs in display.get("section_metric_ids", {}).values():
        displayed.update(refs)
    all_in_ids = {metric["id"] for metric in metrics.values() if metric.get("metric_role") == "technology_spend_total"}
    advertised = displayed & all_in_ids
    if advertised and not isinstance(reconciliation, dict):
        issues.append(_issue(ErrorCode.TECHNOLOGY_SPEND_RECONCILIATION_INVALID, "An advertised technology-spend total requires the typed reconciliation", "$.technology_spend_reconciliation"))
    if document.get("status") == "partial" and advertised:
        issues.append(_issue(ErrorCode.TECHNOLOGY_SPEND_RECONCILIATION_INVALID, "A partial report cannot advertise an all-in technology-spend total", "$.display"))
    if not isinstance(reconciliation, dict):
        return

    input_ids = reconciliation.get("input_metric_ids", [])
    inputs = [metrics.get(metric_id) for metric_id in input_ids]
    if any(metric is None for metric in inputs):
        issues.append(_issue(ErrorCode.DANGLING_REFERENCE, "Technology-spend input does not resolve", "$.technology_spend_reconciliation.input_metric_ids"))
        return
    input_scopes = [metric.get("accounting_boundary", {}).get("scope") for metric in inputs if metric]
    if set(input_scopes) != set(SCOPE_OWNERS) or len(input_scopes) != 3:
        issues.append(_issue(ErrorCode.CANONICAL_SCOPE_MISSING, "Technology spend requires exactly one cloud, direct_ai, and saas metric", "$.technology_spend_reconciliation.input_metric_ids"))
    if len(input_scopes) != len(set(input_scopes)):
        issues.append(_issue(ErrorCode.CANONICAL_SCOPE_DUPLICATE, "Technology-spend inputs contain a duplicate scope", "$.technology_spend_reconciliation.input_metric_ids"))
    if any(not metric.get("accounting_boundary", {}).get("total_eligible") for metric in inputs if metric):
        issues.append(_issue(ErrorCode.ACCOUNTING_BOUNDARY_INELIGIBLE, "Technology-spend reconciliation includes an ineligible scope", "$.technology_spend_reconciliation.input_metric_ids"))
    signatures = {(tuple(sorted(metric.get("period", {}).items())), metric.get("currency"), metric.get("accounting_boundary", {}).get("cost_basis")) for metric in inputs if metric}
    if len(signatures) != 1:
        issues.append(_issue(ErrorCode.CANONICAL_SCOPE_MISMATCH, "Technology-spend inputs must have identical period, timezone, currency, and cost basis", "$.technology_spend_reconciliation.input_metric_ids"))
    output = metrics.get(reconciliation.get("output_metric_id"))
    if output is None:
        issues.append(_issue(ErrorCode.DANGLING_REFERENCE, "Technology-spend output does not resolve", "$.technology_spend_reconciliation.output_metric_id"))
        return
    if output.get("metric_role") != "technology_spend_total" or output.get("basis") != "calculated" or set(output.get("input_metric_ids", [])) != set(input_ids) or not output.get("formula"):
        issues.append(_issue(ErrorCode.TECHNOLOGY_SPEND_RECONCILIATION_INVALID, "Technology-spend output must be a calculated total with the exact canonical inputs and formula", "$.technology_spend_reconciliation.output_metric_id"))
    values = [metric.get("value") for metric in inputs if metric]
    if all(isinstance(value, (int, float)) for value in values) and isinstance(output.get("value"), (int, float)):
        difference = round(output["value"] - sum(values), 6)
        tolerance = reconciliation.get("tolerance", 0)
        if reconciliation.get("status") != "passed" or abs(difference) > tolerance or abs(reconciliation.get("difference", 0) - difference) > tolerance:
            issues.append(_issue(ErrorCode.TECHNOLOGY_SPEND_RECONCILIATION_INVALID, "Technology-spend total does not reconcile within tolerance", "$.technology_spend_reconciliation"))


def validate_verified_outcome(document: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    currencies = {document.get(key, {}).get("currency") for key in ("baseline", "observed_post_change", "verified_amount")}
    if len(currencies) > 1:
        issues.append(_issue(ErrorCode.RECONCILIATION_FAILED, "Verified outcome amounts must use one currency", "$"))
    expected = round(document.get("baseline", {}).get("amount", 0) - document.get("observed_post_change", {}).get("amount", 0), 2)
    actual = round(document.get("verified_amount", {}).get("amount", 0), 2)
    if expected != actual:
        issues.append(_issue(ErrorCode.RECONCILIATION_FAILED, f"Verified amount {actual} does not equal baseline minus post-change amount {expected}", "$.verified_amount.amount"))
    return issues


def validate_semantics(document: dict[str, Any]) -> list[ValidationIssue]:
    document_type = document.get("document_type")
    if document_type == "tool_result":
        return validate_tool_result(document)
    if document_type == "trusted_report":
        return validate_trusted_report(document)
    if document_type == "verified_outcome":
        return validate_verified_outcome(document)
    return []
