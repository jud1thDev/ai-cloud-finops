"""Tests for auto-generation mode."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from finops_sim.catalog.selector import select_scenarios
from finops_sim.generators.orchestrator import generate_auto


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    return tmp_path / "output"


class TestSelectScenarios:
    def test_select_l1(self) -> None:
        selected = select_scenarios("L1", 5, seed=42)
        assert len(selected) == 5
        assert all(s.level.value == "L1" for s in selected)

    def test_select_more_than_available(self) -> None:
        # L1 has 13 scenarios
        selected = select_scenarios("L1", 100, seed=42)
        assert len(selected) == 13

    def test_reproducible(self) -> None:
        s1 = select_scenarios("L2", 3, seed=42)
        s2 = select_scenarios("L2", 3, seed=42)
        assert [s.id for s in s1] == [s.id for s in s2]

    def test_sorted_by_id(self) -> None:
        selected = select_scenarios("L1", 5, seed=42)
        ids = [s.id for s in selected]
        assert ids == sorted(ids)


class TestGenerateAuto:
    def test_auto_generates_multiple(self, tmp_output: Path) -> None:
        results = generate_auto("L1", 3, str(tmp_output), seed=42)
        assert len(results) == 3

        for r in results:
            out_dir = Path(r["output_dir"])
            assert (out_dir / "main.tf").exists()
            assert (out_dir / "metrics" / "metrics.json").exists()
            assert (out_dir / "cost_report.json").exists()
            assert (out_dir / "answer.json").exists()
            assert (out_dir / "scoring_rubric.json").exists()
            assert (out_dir / "README.md").exists()

    def test_auto_same_company_across_scenarios(self, tmp_output: Path) -> None:
        results = generate_auto("L1", 3, str(tmp_output), seed=42)
        companies = {r["company"] for r in results}
        assert len(companies) == 1  # same company for all

    def test_auto_different_scenario_ids(self, tmp_output: Path) -> None:
        results = generate_auto("L1", 3, str(tmp_output), seed=42)
        ids = [r["scenario_id"] for r in results]
        assert len(set(ids)) == 3
