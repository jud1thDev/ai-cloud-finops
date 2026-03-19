"""E2E tests: generate + validate for L1/L2/L3 scenarios."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from finops_sim.generators.orchestrator import generate_auto, generate_fixed
from finops_sim.utils.validators import validate_output_dir


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    return tmp_path / "output"


class TestE2EFixed:
    """E2E: generate fixed → validate for one scenario per level."""

    @pytest.mark.parametrize(
        "scenario_id",
        ["L1-001", "L1-005", "L1-011"],
    )
    def test_l1_scenarios(self, tmp_output: Path, scenario_id: str) -> None:
        result = generate_fixed(scenario_id, str(tmp_output), seed=42)
        errors = validate_output_dir(Path(result["output_dir"]))
        assert errors == [], "Validation errors for %s: %s" % (scenario_id, errors)

    @pytest.mark.parametrize(
        "scenario_id",
        ["L2-014", "L2-019", "L2-021"],
    )
    def test_l2_scenarios(self, tmp_output: Path, scenario_id: str) -> None:
        result = generate_fixed(scenario_id, str(tmp_output), seed=42)
        errors = validate_output_dir(Path(result["output_dir"]))
        assert errors == [], "Validation errors for %s: %s" % (scenario_id, errors)

    @pytest.mark.parametrize(
        "scenario_id",
        ["L3-025", "L3-031", "L3-035"],
    )
    def test_l3_scenarios(self, tmp_output: Path, scenario_id: str) -> None:
        result = generate_fixed(scenario_id, str(tmp_output), seed=42)
        errors = validate_output_dir(Path(result["output_dir"]))
        assert errors == [], "Validation errors for %s: %s" % (scenario_id, errors)


class TestE2EAutoMode:
    """E2E: auto-generate → validate."""

    def test_auto_l1(self, tmp_output: Path) -> None:
        results = generate_auto("L1", 3, str(tmp_output), seed=42)
        for r in results:
            errors = validate_output_dir(Path(r["output_dir"]))
            assert errors == [], "Validation errors for %s: %s" % (
                r["scenario_id"],
                errors,
            )

    def test_auto_l2(self, tmp_output: Path) -> None:
        results = generate_auto("L2", 3, str(tmp_output), seed=99)
        for r in results:
            errors = validate_output_dir(Path(r["output_dir"]))
            assert errors == [], "Validation errors for %s: %s" % (
                r["scenario_id"],
                errors,
            )

    def test_auto_l3(self, tmp_output: Path) -> None:
        results = generate_auto("L3", 3, str(tmp_output), seed=77)
        for r in results:
            errors = validate_output_dir(Path(r["output_dir"]))
            assert errors == [], "Validation errors for %s: %s" % (
                r["scenario_id"],
                errors,
            )


class TestE2EOutputContent:
    """E2E: verify output content consistency across artifacts."""

    def test_scenario_id_consistent(self, tmp_output: Path) -> None:
        """All generated files reference the same scenario ID."""
        result = generate_fixed("L1-003", str(tmp_output), seed=42)
        out = Path(result["output_dir"])

        metrics = json.loads((out / "metrics" / "metrics.json").read_text())
        answer = json.loads((out / "answer.json").read_text())
        rubric = json.loads((out / "scoring_rubric.json").read_text())
        cost = json.loads((out / "cost_report.json").read_text())

        assert metrics["metadata"]["scenario_id"] == "L1-003"
        assert answer["scenario_id"] == "L1-003"
        assert rubric["scenario_id"] == "L1-003"
        assert cost["scenario_id"] == "L1-003"

    def test_resource_count_matches(self, tmp_output: Path) -> None:
        """Number of resources in metrics matches manifest count."""
        result = generate_fixed("L1-001", str(tmp_output), seed=42)
        out = Path(result["output_dir"])

        metrics = json.loads((out / "metrics" / "metrics.json").read_text())
        assert len(metrics["resources"]) == result["resource_count"]

    def test_answer_resources_are_problems_only(self, tmp_output: Path) -> None:
        """Answer affected_resources should only include problem resources."""
        result = generate_fixed("L1-001", str(tmp_output), seed=42)
        out = Path(result["output_dir"])

        answer = json.loads((out / "answer.json").read_text())
        assert len(answer["affected_resources"]) == result["problem_count"]

    def test_readme_contains_company_name(self, tmp_output: Path) -> None:
        result = generate_fixed("L2-014", str(tmp_output), seed=42)
        out = Path(result["output_dir"])
        readme = (out / "README.md").read_text()
        assert result["company"] in readme
