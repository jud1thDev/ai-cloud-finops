"""Validate example outputs against the output schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SPEC_DIR = Path(__file__).resolve().parent.parent / "spec"
SCHEMA_PATH = SPEC_DIR / "output_schema.json"
EXAMPLES_DIR = SPEC_DIR / "examples"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture
def schema():
    return _load_json(SCHEMA_PATH)


@pytest.fixture
def validator(schema):
    jsonschema = pytest.importorskip("jsonschema")
    return jsonschema.Draft7Validator(schema)


class TestSchemaExamples:
    """Example JSON files must pass schema validation."""

    @pytest.mark.parametrize("level", ["L1", "L2", "L3"])
    def test_example_valid(self, validator, level):
        path = EXAMPLES_DIR / f"{level}_output.json"
        data = _load_json(path)
        errors = list(validator.iter_errors(data))
        assert errors == [], f"{level} errors: {[e.message for e in errors]}"

    def test_l1_has_required_fields(self):
        data = _load_json(EXAMPLES_DIR / "L1_output.json")
        assert "analysis" in data
        assert "problems_found" in data["analysis"]
        assert "recommendations" in data
        assert "summary" in data

    def test_l2_has_unit_economics(self):
        data = _load_json(EXAMPLES_DIR / "L2_output.json")
        assert "unit_economics" in data["analysis"]
        ue = data["analysis"]["unit_economics"]
        assert "cost_per_1k_requests" in ue
        assert "cost_per_order" in ue
        assert "trend" in ue
        assert "vs_previous_period" in ue

    def test_l3_has_all_fields(self):
        data = _load_json(EXAMPLES_DIR / "L3_output.json")
        assert "unit_economics" in data["analysis"]
        assert "elasticity" in data["analysis"]
        assert "alerts" in data
        assert len(data["alerts"]) > 0

    def test_schema_rejects_bad_output(self, validator):
        """A minimal invalid document should have errors."""
        bad = {"analysis": {"problems_found": "not_an_array"}}
        errors = list(validator.iter_errors(bad))
        assert len(errors) > 0
