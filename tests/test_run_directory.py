from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

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
    documents = [
        json.loads((fixture_root / "cloud-scope.json").read_text()),
        json.loads((fixture_root / "direct_ai-scope.json").read_text()),
        json.loads((fixture_root / "saas-scope.json").read_text()),
        json.loads((fixture_root / "technology-spend-report.json").read_text()),
    ]
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
    for producer in ("finops-watchdog", "recovery-economics"):
        artifacts.append({
            "producer": {"name": producer, "version": "0.0.0"},
            "document_type": "tool_result",
            "relative_path": f"{producer}/result.json",
            "content_sha256": "0" * 64,
            "status": "omitted",
            "contract_valid": False,
            "omission_reason": "Not required for focused boundary provenance fixture.",
        })
    manifest = {
        "contract": "ccac/1.1.0",
        "document_type": "pipeline_manifest",
        "run_id": documents[0]["run_id"],
        "mode": "illustrative",
        "started_at": "2026-08-07T12:00:00Z",
        "completed_at": "2026-08-07T12:01:00Z",
        "status": "partial",
        "required_producers": [*PRODUCERS, "tech-spend-command-center"],
        "artifacts": artifacts,
        "errors": [],
    }
    write_json(tmp_path / "manifest.json", manifest)
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
