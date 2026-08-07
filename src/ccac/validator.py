from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .errors import ErrorCode, ValidationIssue
from .schema import validate_structure
from .semantic import validate_semantics


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
        issues.extend(validate_document(document))
        if document.get("run_id") != run_id:
            issues.append(ValidationIssue(ErrorCode.RUN_ID_MISMATCH, f"Artifact run_id differs from manifest: {relative_path}", f"{path}.run_id"))
        if document.get("mode") != mode:
            issues.append(ValidationIssue(ErrorCode.MODE_MISMATCH, f"Artifact mode differs from manifest: {relative_path}", f"{path}.mode"))
    return issues

