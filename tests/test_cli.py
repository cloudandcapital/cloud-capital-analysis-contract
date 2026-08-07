from __future__ import annotations

import json
from pathlib import Path

from ccac.cli import main


ROOT = Path(__file__).resolve().parents[1]


def test_cli_valid_file(capsys):
    result = main(["validate", str(ROOT / "fixtures/valid/minimal-finops-lite-result.json")])
    assert result == 0
    assert "passed" in capsys.readouterr().out


def test_cli_invalid_file_returns_two(tmp_path, capsys):
    target = tmp_path / "bad.json"
    target.write_text(json.dumps({"document_type": "tool_result"}))
    result = main(["validate", str(target), "--format", "json"])
    assert result == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
    assert payload["issues"][0]["code"] == "SCHEMA_INVALID"
