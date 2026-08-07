from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from ccac.errors import ErrorCode
from ccac.validator import validate_run_directory


PRODUCERS = [
    "finops-lite",
    "finops-watchdog",
    "recovery-economics",
    "ai-cost-lens",
    "saas-cost-analyzer",
]
ROOT = Path(__file__).resolve().parents[1]


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_run(tmp_path, valid_tool_result, valid_report):
    artifacts = []
    for producer in PRODUCERS:
        payload = deepcopy(valid_tool_result)
        payload["producer"] = {"name": producer, "version": "1.0.0"}
        relative = f"{producer}/result.json"
        digest = write_json(tmp_path / relative, payload)
        artifacts.append({
            "producer": payload["producer"],
            "document_type": "tool_result",
            "relative_path": relative,
            "content_sha256": digest,
            "status": "produced",
            "contract_valid": True,
            "omission_reason": None,
        })
    relative = "tech-spend-command-center/report.json"
    digest = write_json(tmp_path / relative, valid_report)
    artifacts.append({
        "producer": valid_report["producer"],
        "document_type": "trusted_report",
        "relative_path": relative,
        "content_sha256": digest,
        "status": "produced",
        "contract_valid": True,
        "omission_reason": None,
    })
    manifest = {
        "contract": "ccac/1.0.0",
        "document_type": "pipeline_manifest",
        "run_id": valid_tool_result["run_id"],
        "mode": "illustrative",
        "started_at": "2026-08-04T12:00:00Z",
        "completed_at": "2026-08-04T12:01:00Z",
        "status": "complete",
        "required_producers": [*PRODUCERS, "tech-spend-command-center"],
        "artifacts": artifacts,
        "errors": [],
    }
    write_json(tmp_path / "manifest.json", manifest)
    return manifest


def make_1_1_run(tmp_path):
    fixture_root = ROOT / "fixtures" / "valid" / "1.1.0"
    scope_documents = [
        json.loads((fixture_root / "cloud-scope.json").read_text()),
        json.loads((fixture_root / "direct_ai-scope.json").read_text()),
        json.loads((fixture_root / "saas-scope.json").read_text()),
    ]
    for document in scope_documents:
        document["producer"]["version"] = "1.0.0"
    support_documents = []
    for producer in ("finops-watchdog", "recovery-economics"):
        document = deepcopy(scope_documents[0])
        document["producer"] = {"name": producer, "version": "1.0.0"}
        document["metrics"] = []
        document["findings"] = []
        document["opportunities"] = []
        support_documents.append(document)
    report = json.loads((fixture_root / "technology-spend-report.json").read_text())
    documents = [*scope_documents[:1], *support_documents, *scope_documents[1:], report]
    artifacts = []
    for document in documents:
        producer = document["producer"]
        relative = f"{producer['name']}/{'report' if document['document_type'] == 'trusted_report' else 'result'}.json"
        digest = write_json(tmp_path / relative, document)
        artifacts.append({
            "producer": producer,
            "document_type": document["document_type"],
            "relative_path": relative,
            "content_sha256": digest,
            "status": "produced",
            "contract_valid": True,
            "omission_reason": None,
        })
    manifest = {
        "contract": "ccac/1.1.0",
        "document_type": "pipeline_manifest",
        "run_id": documents[0]["run_id"],
        "mode": "illustrative",
        "started_at": "2026-08-07T12:00:00Z",
        "completed_at": "2026-08-07T12:01:00Z",
        "status": "complete",
        "required_producers": [*PRODUCERS, "tech-spend-command-center"],
        "artifacts": artifacts,
        "errors": [],
    }
    write_json(tmp_path / "manifest.json", manifest)
    return manifest


def artifact_for(manifest, producer):
    return next(item for item in manifest["artifacts"] if item["producer"]["name"] == producer)


def rewrite_artifact(tmp_path, manifest, producer, payload):
    artifact = artifact_for(manifest, producer)
    artifact["content_sha256"] = write_json(tmp_path / artifact["relative_path"], payload)
    write_json(tmp_path / "manifest.json", manifest)


def make_truthful_partial_1_1_run(tmp_path):
    manifest = make_1_1_run(tmp_path)
    manifest["status"] = "partial"
    watchdog = artifact_for(manifest, "finops-watchdog")
    watchdog["status"] = "omitted"
    watchdog["contract_valid"] = False
    watchdog["omission_reason"] = "Watchdog result unavailable."
    report_artifact = artifact_for(manifest, "tech-spend-command-center")
    report_path = tmp_path / report_artifact["relative_path"]
    report = json.loads(report_path.read_text())
    report["status"] = "partial"
    report["included_producers"] = [item for item in report["included_producers"] if item["name"] != "finops-watchdog"]
    report["producer_quality"] = [item for item in report["producer_quality"] if item["producer"]["name"] != "finops-watchdog"]
    report["omitted_producers"] = [{"name": "finops-watchdog", "reason": "Watchdog result unavailable."}]
    report["metric_catalog"] = report["metric_catalog"][:-1]
    report["display"]["headline_metric_ids"] = ["metric.tech-spend.scope.cloud"]
    report["reconciliation"] = [{
        "id": "reconciliation.available-cloud",
        "assertion": "Displayed Cloud metric is unchanged.",
        "input_metric_ids": ["metric.tech-spend.scope.cloud"],
        "output_metric_id": "metric.tech-spend.scope.cloud",
        "difference": 0,
        "tolerance": 0,
        "status": "passed",
    }]
    rewrite_artifact(tmp_path, manifest, "tech-spend-command-center", report)
    return manifest


def test_complete_run_directory_passes(tmp_path, valid_tool_result, valid_report):
    make_run(tmp_path, valid_tool_result, valid_report)
    assert validate_run_directory(tmp_path) == []


def test_hash_mismatch_fails_before_trusting_artifact(tmp_path, valid_tool_result, valid_report):
    manifest = make_run(tmp_path, valid_tool_result, valid_report)
    target = tmp_path / manifest["artifacts"][0]["relative_path"]
    target.write_text(target.read_text() + "\n", encoding="utf-8")
    codes = {issue.code for issue in validate_run_directory(tmp_path)}
    assert ErrorCode.ARTIFACT_HASH_MISMATCH in codes


def test_run_id_mismatch_fails(tmp_path, valid_tool_result, valid_report):
    manifest = make_run(tmp_path, valid_tool_result, valid_report)
    artifact = manifest["artifacts"][0]
    target = tmp_path / artifact["relative_path"]
    payload = json.loads(target.read_text())
    payload["run_id"] = "223e4567-e89b-12d3-a456-426614174000"
    artifact["content_sha256"] = write_json(target, payload)
    write_json(tmp_path / "manifest.json", manifest)
    codes = {issue.code for issue in validate_run_directory(tmp_path)}
    assert ErrorCode.RUN_ID_MISMATCH in codes


def test_missing_artifact_fails(tmp_path, valid_tool_result, valid_report):
    manifest = make_run(tmp_path, valid_tool_result, valid_report)
    target = tmp_path / manifest["artifacts"][0]["relative_path"]
    target.unlink()
    codes = {issue.code for issue in validate_run_directory(tmp_path)}
    assert ErrorCode.ARTIFACT_MISSING in codes


def test_1_1_run_proves_canonical_producer_provenance(tmp_path):
    make_1_1_run(tmp_path)
    assert validate_run_directory(tmp_path) == []


def test_run_contract_mismatch_fails(tmp_path, valid_tool_result, valid_report):
    manifest = make_run(tmp_path, valid_tool_result, valid_report)
    artifact = manifest["artifacts"][0]
    target = tmp_path / artifact["relative_path"]
    payload = json.loads(target.read_text())
    payload["contract"] = "ccac/1.1.0"
    artifact["content_sha256"] = write_json(target, payload)
    write_json(tmp_path / "manifest.json", manifest)
    codes = {issue.code for issue in validate_run_directory(tmp_path)}
    assert ErrorCode.CONTRACT_MISMATCH in codes


def test_1_1_manifest_rejects_1_0_artifact(tmp_path):
    manifest = make_1_1_run(tmp_path)
    artifact = manifest["artifacts"][0]
    target = tmp_path / artifact["relative_path"]
    payload = json.loads(target.read_text())
    payload["contract"] = "ccac/1.0.0"
    artifact["content_sha256"] = write_json(target, payload)
    write_json(tmp_path / "manifest.json", manifest)
    codes = {issue.code for issue in validate_run_directory(tmp_path)}
    assert ErrorCode.CONTRACT_MISMATCH in codes


def test_missing_canonical_source_fails(tmp_path):
    manifest = make_1_1_run(tmp_path)
    artifact = next(item for item in manifest["artifacts"] if item["producer"]["name"] == "finops-lite")
    artifact["status"] = "omitted"
    artifact["contract_valid"] = False
    artifact["omission_reason"] = "Hostile fixture removes canonical source."
    write_json(tmp_path / "manifest.json", manifest)
    codes = {issue.code for issue in validate_run_directory(tmp_path)}
    assert ErrorCode.CANONICAL_SCOPE_SOURCE_MISSING in codes


def test_reinterpreted_canonical_source_fails(tmp_path):
    manifest = make_1_1_run(tmp_path)
    artifact = next(item for item in manifest["artifacts"] if item["producer"]["name"] == "tech-spend-command-center")
    target = tmp_path / artifact["relative_path"]
    payload = json.loads(target.read_text())
    payload["metric_catalog"][0]["value"] = 999
    artifact["content_sha256"] = write_json(target, payload)
    write_json(tmp_path / "manifest.json", manifest)
    codes = {issue.code for issue in validate_run_directory(tmp_path)}
    assert ErrorCode.CANONICAL_SCOPE_SOURCE_MISMATCH in codes


def test_duplicate_canonical_source_fails(tmp_path):
    manifest = make_1_1_run(tmp_path)
    original = next(item for item in manifest["artifacts"] if item["producer"]["name"] == "finops-lite")
    duplicate = deepcopy(original)
    duplicate["relative_path"] = "finops-lite/duplicate.json"
    source = tmp_path / original["relative_path"]
    duplicate["content_sha256"] = write_json(tmp_path / duplicate["relative_path"], json.loads(source.read_text()))
    manifest["artifacts"].append(duplicate)
    write_json(tmp_path / "manifest.json", manifest)
    codes = {issue.code for issue in validate_run_directory(tmp_path)}
    assert ErrorCode.CANONICAL_SCOPE_SOURCE_MISMATCH in codes


def test_partial_manifest_cannot_contain_complete_report(tmp_path):
    manifest = make_1_1_run(tmp_path)
    manifest["status"] = "partial"
    write_json(tmp_path / "manifest.json", manifest)
    assert ErrorCode.RUN_STATUS_MISMATCH in {issue.code for issue in validate_run_directory(tmp_path)}


def test_omitted_producer_cannot_remain_included(tmp_path):
    manifest = make_1_1_run(tmp_path)
    artifact = artifact_for(manifest, "finops-watchdog")
    artifact["status"] = "omitted"
    artifact["contract_valid"] = False
    artifact["omission_reason"] = "Hostile omission."
    write_json(tmp_path / "manifest.json", manifest)
    assert ErrorCode.REPORT_RUN_INVENTORY_MISMATCH in {issue.code for issue in validate_run_directory(tmp_path)}


def test_omitted_producer_cannot_have_valid_quality_summary(tmp_path):
    manifest = make_truthful_partial_1_1_run(tmp_path)
    report_artifact = artifact_for(manifest, "tech-spend-command-center")
    report = json.loads((tmp_path / report_artifact["relative_path"]).read_text())
    report["producer_quality"].append({
        "producer": {"name": "finops-watchdog", "version": "1.0.0"},
        "quality": {"status": "valid", "issues": []},
    })
    rewrite_artifact(tmp_path, manifest, "tech-spend-command-center", report)
    assert ErrorCode.REPORT_RUN_INVENTORY_MISMATCH in {issue.code for issue in validate_run_directory(tmp_path)}


def test_produced_artifact_must_be_included(tmp_path):
    manifest = make_1_1_run(tmp_path)
    report_artifact = artifact_for(manifest, "tech-spend-command-center")
    report = json.loads((tmp_path / report_artifact["relative_path"]).read_text())
    report["included_producers"] = [item for item in report["included_producers"] if item["name"] != "finops-watchdog"]
    report["producer_quality"] = [item for item in report["producer_quality"] if item["producer"]["name"] != "finops-watchdog"]
    report["omitted_producers"] = [{"name": "finops-watchdog", "reason": "Falsely omitted."}]
    rewrite_artifact(tmp_path, manifest, "tech-spend-command-center", report)
    assert ErrorCode.REPORT_RUN_INVENTORY_MISMATCH in {issue.code for issue in validate_run_directory(tmp_path)}


def test_included_producer_version_must_match_artifact(tmp_path):
    manifest = make_1_1_run(tmp_path)
    report_artifact = artifact_for(manifest, "tech-spend-command-center")
    report = json.loads((tmp_path / report_artifact["relative_path"]).read_text())
    report["included_producers"][0]["version"] = "9.9.9"
    rewrite_artifact(tmp_path, manifest, "tech-spend-command-center", report)
    assert ErrorCode.REPORT_RUN_INVENTORY_MISMATCH in {issue.code for issue in validate_run_directory(tmp_path)}


@pytest.mark.parametrize(
    "field,value",
    [
        ("name", "finops-watchdog"),
        ("version", "9.9.9"),
    ],
)
def test_manifest_producer_metadata_must_match_document(tmp_path, field, value):
    manifest = make_1_1_run(tmp_path)
    artifact_for(manifest, "finops-lite")["producer"][field] = value
    write_json(tmp_path / "manifest.json", manifest)
    assert ErrorCode.MANIFEST_ARTIFACT_METADATA_MISMATCH in {issue.code for issue in validate_run_directory(tmp_path)}


def test_manifest_document_type_must_match_document(tmp_path):
    manifest = make_1_1_run(tmp_path)
    artifact_for(manifest, "finops-lite")["document_type"] = "trusted_report"
    write_json(tmp_path / "manifest.json", manifest)
    assert ErrorCode.MANIFEST_ARTIFACT_METADATA_MISMATCH in {issue.code for issue in validate_run_directory(tmp_path)}


def test_valid_produced_artifact_cannot_be_marked_contract_invalid(tmp_path):
    manifest = make_1_1_run(tmp_path)
    artifact_for(manifest, "finops-lite")["contract_valid"] = False
    write_json(tmp_path / "manifest.json", manifest)
    assert ErrorCode.MANIFEST_ARTIFACT_METADATA_MISMATCH in {issue.code for issue in validate_run_directory(tmp_path)}


def test_invalid_artifact_cannot_be_marked_contract_valid(tmp_path):
    manifest = make_1_1_run(tmp_path)
    artifact = artifact_for(manifest, "finops-lite")
    target = tmp_path / artifact["relative_path"]
    payload = json.loads(target.read_text())
    del payload["period"]
    artifact["content_sha256"] = write_json(target, payload)
    write_json(tmp_path / "manifest.json", manifest)
    assert ErrorCode.MANIFEST_ARTIFACT_METADATA_MISMATCH in {issue.code for issue in validate_run_directory(tmp_path)}


def test_producer_cannot_be_included_and_omitted(tmp_path):
    manifest = make_1_1_run(tmp_path)
    report_artifact = artifact_for(manifest, "tech-spend-command-center")
    report = json.loads((tmp_path / report_artifact["relative_path"]).read_text())
    report["omitted_producers"] = [{"name": "finops-lite", "reason": "Contradictory hostile inventory."}]
    rewrite_artifact(tmp_path, manifest, "tech-spend-command-center", report)
    assert ErrorCode.REPORT_RUN_INVENTORY_MISMATCH in {issue.code for issue in validate_run_directory(tmp_path)}


def test_complete_manifest_requires_every_analytical_producer(tmp_path):
    manifest = make_1_1_run(tmp_path)
    artifact = artifact_for(manifest, "recovery-economics")
    artifact["status"] = "omitted"
    artifact["contract_valid"] = False
    artifact["omission_reason"] = "Hostile omission."
    write_json(tmp_path / "manifest.json", manifest)
    assert ErrorCode.RUN_STATUS_MISMATCH in {issue.code for issue in validate_run_directory(tmp_path)}


@pytest.mark.parametrize("failure", ["failed", "hash_invalid"])
def test_complete_report_rejects_failed_or_hash_invalid_producer(tmp_path, failure):
    manifest = make_1_1_run(tmp_path)
    artifact = artifact_for(manifest, "finops-watchdog")
    if failure == "failed":
        artifact["status"] = "failed"
        artifact["contract_valid"] = False
        artifact["omission_reason"] = "Hostile failure."
        write_json(tmp_path / "manifest.json", manifest)
    else:
        target = tmp_path / artifact["relative_path"]
        target.write_text(target.read_text() + "\n")
    assert ErrorCode.RUN_STATUS_MISMATCH in {issue.code for issue in validate_run_directory(tmp_path)}


def test_truthful_partial_run_passes(tmp_path):
    make_truthful_partial_1_1_run(tmp_path)
    assert validate_run_directory(tmp_path) == []
