"""Validate AI output against the output schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

SCHEMA_PATH = Path(__file__).resolve().parent.parent.parent / "spec" / "output_schema.json"

# Level-specific required fields
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


def load_schema() -> dict:
    """Load the output schema."""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate(data: Dict[str, Any], level: str = "L1") -> List[str]:
    """Validate data against output schema. Returns list of error messages (empty=valid)."""
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema package not installed. Run: pip install jsonschema"]

    schema = load_schema()

    # Validate against base schema (without recursive definitions)
    base_schema = {k: v for k, v in schema.items() if k != "definitions"}
    validator = jsonschema.Draft7Validator(base_schema)
    errors = [f"{e.json_path}: {e.message}" for e in validator.iter_errors(data)]

    # Check level-specific requirements
    level_req = _LEVEL_REQUIREMENTS.get(level, _LEVEL_REQUIREMENTS["L1"])

    for root_field in level_req["root"]:
        if root_field not in data:
            errors.append(f"missing required field for {level}: {root_field}")

    analysis = data.get("analysis", {})
    for field in level_req.get("analysis", []):
        if field not in analysis:
            errors.append(f"missing required field for {level}: analysis.{field}")

    return errors


def validate_file(path: Path, level: str = "L1") -> List[str]:
    """Validate a JSON file against the output schema."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {e}"]
    except FileNotFoundError:
        return [f"File not found: {path}"]

    return validate(data, level)
