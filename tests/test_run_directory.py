from __future__ import annotations

import hashlib
import json
from copy import deepcopy

from ccac.errors import ErrorCode
from ccac.validator import validate_run_directory


PRODUCERS = [
    "finops-lite",
    "finops-watchdog",
    "recovery-economics",
    "ai-cost-lens",
    "saas-cost-analyzer",
]


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
