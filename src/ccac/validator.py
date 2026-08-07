from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .errors import ErrorCode, ValidationIssue
from .schema import validate_structure
from .semantic import validate_semantics


CANONICAL_SCOPE_FIELDS = (
    "id", "value", "unit", "currency", "basis", "additivity", "period", "formula",
    "input_metric_ids", "evidence_ids", "quality_status", "accounting_boundary",
)


def load_json(path: Path) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [ValidationIssue(ErrorCode.INVALID_JSON, str(exc), str(path))]
    if not isinstance(value, dict):
        return None, [ValidationIssue(ErrorCode.INVALID_JSON, "Top-level JSON value must be an object", str(path))]
    return value, []


def validate_document(document: dict[str, Any]) -> list[ValidationIssue]:
    structural = validate_structure(document)
    if structural:
        return structural
    return validate_semantics(document)


def validate_file(path: Path) -> list[ValidationIssue]:
    document, issues = load_json(path)
    return issues if issues else validate_document(document or {})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_run_directory(run_directory: Path) -> list[ValidationIssue]:
    manifest_path = run_directory / "manifest.json"
    if not manifest_path.is_file():
        return [ValidationIssue(ErrorCode.MANIFEST_MISSING, "Run directory does not contain manifest.json", str(manifest_path))]
    manifest, issues = load_json(manifest_path)
    if issues:
        return issues
    assert manifest is not None
    issues.extend(validate_document(manifest))
    if issues:
        return issues

    run_id = manifest["run_id"]
    mode = manifest["mode"]
    contract = manifest["contract"]
    produced_documents: list[dict[str, Any]] = []
    for index, artifact in enumerate(manifest.get("artifacts", [])):
        if artifact.get("status") != "produced":
            continue
        relative_path = artifact["relative_path"]
        artifact_path = run_directory / relative_path
        path = f"$.artifacts[{index}]"
        if not artifact_path.is_file():
            issues.append(ValidationIssue(ErrorCode.ARTIFACT_MISSING, f"Artifact is missing: {relative_path}", path))
            continue
        actual_hash = _sha256(artifact_path)
        if actual_hash != artifact["content_sha256"]:
            issues.append(ValidationIssue(ErrorCode.ARTIFACT_HASH_MISMATCH, f"Artifact hash mismatch for {relative_path}", path, {"expected": artifact["content_sha256"], "actual": actual_hash}))
            continue
        document, load_issues = load_json(artifact_path)
        issues.extend(load_issues)
        if document is None:
            continue
        produced_documents.append(document)
        issues.extend(validate_document(document))
        if document.get("contract") != contract:
            issues.append(ValidationIssue(ErrorCode.CONTRACT_MISMATCH, f"Artifact contract differs from manifest: {relative_path}", f"{path}.contract"))
        if document.get("run_id") != run_id:
            issues.append(ValidationIssue(ErrorCode.RUN_ID_MISMATCH, f"Artifact run_id differs from manifest: {relative_path}", f"{path}.run_id"))
        if document.get("mode") != mode:
            issues.append(ValidationIssue(ErrorCode.MODE_MISMATCH, f"Artifact mode differs from manifest: {relative_path}", f"{path}.mode"))
    if contract == "ccac/1.1.0":
        reports = [document for document in produced_documents if document.get("document_type") == "trusted_report"]
        tool_results = [document for document in produced_documents if document.get("document_type") == "tool_result"]
        for report in reports:
            for index, metric in enumerate(report.get("metric_catalog", [])):
                boundary = metric.get("accounting_boundary")
                if not isinstance(boundary, dict) or boundary.get("relationship") != "canonical_scope_spend":
                    continue
                owner = boundary.get("canonical_owner")
                matches = [
                    source_metric
                    for result in tool_results
                    if result.get("producer", {}).get("name") == owner
                    for source_metric in result.get("metrics", [])
                    if source_metric.get("id") == metric.get("id")
                ]
                path = f"$.metric_catalog[{index}]"
                if not matches:
                    issues.append(ValidationIssue(ErrorCode.CANONICAL_SCOPE_SOURCE_MISSING, f"Canonical scope metric must have exactly one source in owner {owner!r}", path))
                    continue
                if len(matches) > 1:
                    issues.append(ValidationIssue(ErrorCode.CANONICAL_SCOPE_SOURCE_MISMATCH, f"Canonical scope metric has multiple sources in owner {owner!r}", path))
                    continue
                if any(matches[0].get(field) != metric.get(field) for field in CANONICAL_SCOPE_FIELDS):
                    issues.append(ValidationIssue(ErrorCode.CANONICAL_SCOPE_SOURCE_MISMATCH, "Trusted-report canonical scope differs from its producer-owned source", path))
    return issues
