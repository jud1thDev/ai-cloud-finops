"""Tests for TagsInventoryGenerator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from finops_sim.generators.orchestrator import generate_fixed


@pytest.fixture
def tagged_output(tmp_path):
    result = generate_fixed(
        "L1-001",
        str(tmp_path),
        seed=42,
        generators_override={"tags_inventory"},
    )
    return result, tmp_path


class TestTagsInventory:
    def test_file_created(self, tagged_output):
        result, _ = tagged_output
        assert "tags_inventory" in result["files"]
        assert Path(result["files"]["tags_inventory"]).exists()

    def test_problem_resources_have_missing_tags(self, tagged_output):
        result, _ = tagged_output
        data = json.loads(Path(result["files"]["tags_inventory"]).read_text())
        problem_resources = [r for r in data["resources"] if r["is_problem"]]
        assert len(problem_resources) > 0
        for r in problem_resources:
            assert len(r["missing_tags"]) > 0
            assert r["compliance_pct"] < 50

    def test_decoy_resources_fully_compliant(self, tagged_output):
        result, _ = tagged_output
        data = json.loads(Path(result["files"]["tags_inventory"]).read_text())
        decoy_resources = [r for r in data["resources"] if not r["is_problem"]]
        for r in decoy_resources:
            assert r["missing_tags"] == []
            assert r["compliance_pct"] == 100.0

    def test_summary_stats(self, tagged_output):
        result, _ = tagged_output
        data = json.loads(Path(result["files"]["tags_inventory"]).read_text())
        summary = data["summary"]
        assert "total_resources" in summary
        assert "tag_coverage_pct" in summary
        assert summary["total_resources"] > 0
        assert 0 < summary["tag_coverage_pct"] < 100
