from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def valid_tool_result():
    return json.loads((ROOT / "fixtures/valid/minimal-finops-lite-result.json").read_text())


@pytest.fixture
def valid_report():
    return json.loads((ROOT / "fixtures/valid/minimal-trusted-report.json").read_text())


@pytest.fixture
def opportunity():
    return {
        "id": "opportunity.test.one",
        "producer": {"name": "finops-lite", "version": "1.0.0"},
        "opportunity_type": "usage",
        "title": "Review test opportunity",
        "scope": {"resource": "test-one"},
        "estimate": {"basis": "estimated", "period": "monthly", "low": 10, "expected": 20, "high": 30, "currency": "USD", "formula": "observed cost times eligible fraction"},
        "confidence": "medium",
        "evidence_ids": ["evidence.aws.focus.total"],
        "related_finding_ids": [],
        "related_opportunity_ids": [],
        "overlap": {"disposition": "none_known", "group_id": None, "reason": "No overlapping scope found in fixture."},
        "review": {
            "required": True,
            "approval_required": True,
            "rollback_plan_required": True,
            "verification_required": True,
            "non_mutating_review_steps": ["Review the source evidence with the workload owner."],
        },
        "status": "identified",
    }

