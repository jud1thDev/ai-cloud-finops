"""Integration tests: full generation pipeline for sample scenarios."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from finops_sim.generators.orchestrator import generate_fixed


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    return tmp_path / "output"


class TestGenerateFixed:
    def test_l1_001_full_generation(self, tmp_output: Path) -> None:
        result = generate_fixed("L1-001", str(tmp_output), seed=42)

        assert result["scenario_id"] == "L1-001"
        assert result["resource_count"] == 6
        assert result["problem_count"] == 4
        assert result["decoy_count"] == 2

        out_dir = Path(result["output_dir"])

        # main.tf exists and has content
        main_tf = out_dir / "main.tf"
        assert main_tf.exists()
        hcl = main_tf.read_text()
        assert 'provider "aws"' in hcl
        assert "aws_instance" in hcl
        assert "aws_ebs_volume" in hcl

        # metrics.json
        metrics_file = out_dir / "metrics" / "metrics.json"
        assert metrics_file.exists()
        metrics = json.loads(metrics_file.read_text())
        assert metrics["metadata"]["scenario_id"] == "L1-001"
        assert metrics["metadata"]["points_per_series"] == 720
        assert len(metrics["resources"]) == 6

        # answer.json
        answer_file = out_dir / "answer.json"
        assert answer_file.exists()
        answer = json.loads(answer_file.read_text())
        assert answer["severity"] == "medium"
        assert answer["savings_estimate"]["monthly_usd"] == 150.0
        assert len(answer["affected_resources"]) == 4

        # scoring_rubric.json
        rubric_file = out_dir / "scoring_rubric.json"
        assert rubric_file.exists()
        rubric = json.loads(rubric_file.read_text())
        assert rubric["total_points"] == 100

    def test_reproducible_with_same_seed(self, tmp_output: Path) -> None:
        r1 = generate_fixed("L1-001", str(tmp_output / "a"), seed=99)
        r2 = generate_fixed("L1-001", str(tmp_output / "b"), seed=99)

        dir_a = Path(r1["output_dir"])
        dir_b = Path(r2["output_dir"])

        # Same seed → same HCL
        assert (dir_a / "main.tf").read_text() == (dir_b / "main.tf").read_text()
        # Same metrics
        assert (
            (dir_a / "metrics" / "metrics.json").read_text()
            == (dir_b / "metrics" / "metrics.json").read_text()
        )

    def test_different_seed_different_names(self, tmp_output: Path) -> None:
        r1 = generate_fixed("L1-001", str(tmp_output / "a"), seed=1)
        r2 = generate_fixed("L1-001", str(tmp_output / "b"), seed=2)

        dir_a = Path(r1["output_dir"])
        dir_b = Path(r2["output_dir"])

        # Different seeds → different resource names in HCL
        assert (dir_a / "main.tf").read_text() != (dir_b / "main.tf").read_text()

    def test_l2_scenario(self, tmp_output: Path) -> None:
        result = generate_fixed("L2-014", str(tmp_output), seed=42)
        assert result["scenario_id"] == "L2-014"
        out_dir = Path(result["output_dir"])
        assert (out_dir / "main.tf").exists()
        assert (out_dir / "answer.json").exists()

    def test_l3_scenario(self, tmp_output: Path) -> None:
        result = generate_fixed("L3-025", str(tmp_output), seed=42)
        assert result["scenario_id"] == "L3-025"
        out_dir = Path(result["output_dir"])
        assert (out_dir / "main.tf").exists()
        assert (out_dir / "answer.json").exists()
