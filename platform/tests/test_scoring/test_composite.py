"""End-to-end tests for composite scorer using spec examples."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

SPEC_DIR = Path(__file__).resolve().parent.parent.parent / "spec"
EXAMPLES_DIR = SPEC_DIR / "examples"


def _load(name: str) -> dict:
    return json.loads((EXAMPLES_DIR / name).read_text(encoding="utf-8"))


# Mock answer that matches L1 example
MOCK_ANSWER_L1 = {
    "scenario_id": "L1-001",
    "level": "L1",
    "severity": "medium",
    "problem_summary": "중지된 EC2 인스턴스에 연결된 EBS 볼륨 과금",
    "root_cause": "EC2 중지 후 EBS 볼륨 미삭제",
    "recommendation": "스냅샷 생성 후 EBS 볼륨 및 인스턴스 삭제",
    "savings_estimate": {"monthly_usd": 150, "annual_usd": 1800},
    "affected_resources": [
        {"resource_name": "instance-a1b2c3", "resource_type": "aws_instance"},
        {"resource_name": "volume-x1y2z3", "resource_type": "aws_ebs_volume"},
        {"resource_name": "volume-d4e5f6", "resource_type": "aws_ebs_volume"},
        {"resource_name": "volume-g7h8i9", "resource_type": "aws_ebs_volume"},
    ],
}


class TestCompositeScorer:
    def test_l1_example_scores_well(self):
        pytest.importorskip("jsonschema")
        from finops_sim.scoring.composite import score_submission

        submission = _load("L1_output.json")
        result = score_submission(submission, MOCK_ANSWER_L1, "L1")

        assert result["total"] > 0
        assert result["total_max"] > 0
        assert result["percentage"] > 0
        assert "breakdown" in result

    def test_l1_schema_score(self):
        pytest.importorskip("jsonschema")
        from finops_sim.scoring.composite import score_submission

        submission = _load("L1_output.json")
        result = score_submission(submission, MOCK_ANSWER_L1, "L1")
        assert result["breakdown"]["schema"]["score"] == 10

    def test_l1_resource_score(self):
        pytest.importorskip("jsonschema")
        from finops_sim.scoring.composite import score_submission

        submission = _load("L1_output.json")
        result = score_submission(submission, MOCK_ANSWER_L1, "L1")
        resource = result["breakdown"]["resource"]
        assert resource["score"] > 0
        assert resource["recall"] > 0

    def test_l1_savings_score(self):
        pytest.importorskip("jsonschema")
        from finops_sim.scoring.composite import score_submission

        submission = _load("L1_output.json")
        result = score_submission(submission, MOCK_ANSWER_L1, "L1")
        assert result["breakdown"]["savings"]["score"] == 20  # exact match

    def test_l1_economics_skipped(self):
        pytest.importorskip("jsonschema")
        from finops_sim.scoring.composite import score_submission

        submission = _load("L1_output.json")
        result = score_submission(submission, MOCK_ANSWER_L1, "L1")
        assert result["breakdown"]["economics"]["score"] == 0
        assert result["breakdown"]["alerts"]["score"] == 0

    def test_l3_all_dimensions_scored(self):
        pytest.importorskip("jsonschema")
        from finops_sim.scoring.composite import score_submission

        submission = _load("L3_output.json")
        mock_answer = {
            **MOCK_ANSWER_L1,
            "level": "L3",
            "affected_resources": [
                {"resource_name": "eks-nodegroup-general", "resource_type": "aws_eks_node_group"},
                {"resource_name": "nat-gateway-az-a", "resource_type": "aws_nat_gateway"},
                {"resource_name": "rds-replica-read-02", "resource_type": "aws_db_instance"},
            ],
            "savings_estimate": {"monthly_usd": 1462, "annual_usd": 17544},
        }
        result = score_submission(submission, mock_answer, "L3")

        # All dimensions should be active
        for key in ["schema", "resource", "terraform", "savings", "economics", "alerts"]:
            assert key in result["breakdown"]

        # Economics and alerts should have non-zero scores for L3
        assert result["breakdown"]["economics"]["score"] > 0
        assert result["breakdown"]["alerts"]["score"] > 0

    def test_empty_submission_scores_zero(self):
        pytest.importorskip("jsonschema")
        from finops_sim.scoring.composite import score_submission

        result = score_submission({}, MOCK_ANSWER_L1, "L1")
        assert result["total"] < 10
