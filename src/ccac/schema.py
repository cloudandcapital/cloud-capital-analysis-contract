from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .errors import ErrorCode, ValidationIssue


SCHEMA_BY_DOCUMENT_TYPE = {
    "tool_result": "tool-result.schema.json",
    "pipeline_manifest": "pipeline-manifest.schema.json",
    "trusted_report": "trusted-report.schema.json",
    "verified_outcome": "verified-outcome.schema.json",
}


@lru_cache(maxsize=1)
def _schemas() -> dict[str, dict[str, Any]]:
    packaged_root = files("ccac.schemas")
    development_root = Path(__file__).resolve().parents[2] / "schemas"
    schema_root = development_root if development_root.is_dir() else packaged_root
    names = ["common.schema.json", *SCHEMA_BY_DOCUMENT_TYPE.values()]
    loaded = {name: json.loads(schema_root.joinpath(name).read_text(encoding="utf-8")) for name in names}
    return loaded


@lru_cache(maxsize=None)
def _validator(document_type: str) -> Draft202012Validator:
    schemas = _schemas()
    schema = schemas[SCHEMA_BY_DOCUMENT_TYPE[document_type]]
    registry = Registry().with_resources(
        (candidate["$id"], Resource.from_contents(candidate)) for candidate in schemas.values()
    )
    return Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())


def validate_structure(document: dict[str, Any]) -> list[ValidationIssue]:
    document_type = document.get("document_type")
    if document_type not in SCHEMA_BY_DOCUMENT_TYPE:
        return [ValidationIssue(ErrorCode.UNKNOWN_DOCUMENT_TYPE, f"Unsupported document_type: {document_type!r}", "$.document_type")]
    issues = []
    for error in sorted(_validator(document_type).iter_errors(document), key=lambda item: list(item.absolute_path)):
        path = "$" + "".join(f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.absolute_path)
        issues.append(ValidationIssue(ErrorCode.SCHEMA_INVALID, error.message, path))
    return issues
