"""Score JSON Schema validity of AI output (10 points)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "spec" / "output_schema.json"

# Level-specific required fields (checked separately to avoid recursive $ref)
_LEVEL_REQUIREMENTS = {
    "L1": {
        "root": ["analysis", "recommendations", "summary"],
        "analysis": ["problems_found"],
    },
    "L2": {
        "root": ["analysis", "recommendations", "summary"],
        "analysis": ["problems_found", "unit_economics"],
    },
    "L3": {
        "root": ["analysis", "recommendations", "alerts", "summary"],
        "analysis": ["problems_found", "unit_economics", "elasticity"],
    },
}


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def score(submission: Dict[str, Any], level: str = "L1") -> Dict[str, Any]:
    """Validate submission against output schema. Returns max 10 points."""
    try:
        import jsonschema
    except ImportError:
        return {"score": 0, "max": 10, "detail": "jsonschema not installed"}

    schema = _load_schema()

    # Validate against base schema (without recursive definitions)
    base_schema = {k: v for k, v in schema.items() if k != "definitions"}
    errors = list(jsonschema.Draft7Validator(base_schema).iter_errors(submission))

    # Check level-specific requirements
    level_req = _LEVEL_REQUIREMENTS.get(level, _LEVEL_REQUIREMENTS["L1"])
    level_errors = []

    for root_field in level_req["root"]:
        if root_field not in submission:
            level_errors.append(f"missing required field: {root_field}")

    analysis = submission.get("analysis", {})
    for analysis_field in level_req.get("analysis", []):
        if analysis_field not in analysis:
            level_errors.append(f"missing analysis.{analysis_field}")

    all_errors = [e.message for e in errors] + level_errors

    if not all_errors:
        return {"score": 10, "max": 10, "errors": []}

    # Partial credit: deduct 2 per error, min 0
    deduction = min(len(all_errors) * 2, 10)
    return {
        "score": max(0, 10 - deduction),
        "max": 10,
        "errors": all_errors[:5],
    }
