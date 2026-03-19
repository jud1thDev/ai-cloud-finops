"""Tests for catalog loading and validation."""

from pathlib import Path

import pytest

from finops_sim.catalog.loader import (
    get_scenario,
    list_scenarios,
    load_all_scenarios,
    load_scenario_file,
)
from finops_sim.generators.base import Level, ScenarioDefinition


class TestLoadAllScenarios:
    def test_loads_40_scenarios(self, scenarios_dir: Path) -> None:
        catalog = load_all_scenarios(scenarios_dir)
        assert len(catalog) == 40, (
            f"Expected 40 scenarios, got {len(catalog)}: {sorted(catalog.keys())}"
        )

    def test_no_duplicate_ids(self, scenarios_dir: Path) -> None:
        # load_all_scenarios raises on duplicates, so just call it
        catalog = load_all_scenarios(scenarios_dir)
        assert len(catalog) == len(set(catalog.keys()))

    def test_all_levels_present(self, scenarios_dir: Path) -> None:
        catalog = load_all_scenarios(scenarios_dir)
        levels = {s.level for s in catalog.values()}
        assert levels == {Level.L1, Level.L2, Level.L3}

    def test_level_counts(self, scenarios_dir: Path) -> None:
        catalog = load_all_scenarios(scenarios_dir)
        l1 = [s for s in catalog.values() if s.level == Level.L1]
        l2 = [s for s in catalog.values() if s.level == Level.L2]
        l3 = [s for s in catalog.values() if s.level == Level.L3]
        assert len(l1) == 13, f"L1: expected 13, got {len(l1)}"
        assert len(l2) == 11, f"L2: expected 11, got {len(l2)}"
        assert len(l3) == 16, f"L3: expected 16, got {len(l3)}"


class TestScenarioValidation:
    def test_each_scenario_has_required_fields(self, scenarios_dir: Path) -> None:
        catalog = load_all_scenarios(scenarios_dir)
        for sid, s in catalog.items():
            assert s.id == sid
            assert s.title, f"{sid}: missing title"
            assert s.category, f"{sid}: missing category"
            assert s.aws_services, f"{sid}: missing aws_services"
            assert s.description, f"{sid}: missing description"
            assert s.detection_method, f"{sid}: missing detection_method"
            assert s.problem_resources, f"{sid}: missing problem resources"
            assert s.cost_profile.monthly_waste_usd > 0, f"{sid}: waste must be > 0"
            assert s.answer.severity in (
                "low",
                "medium",
                "high",
                "critical",
            ), f"{sid}: invalid severity"
            assert s.scoring.total == 100, f"{sid}: scoring total={s.scoring.total}"

    def test_id_format(self, scenarios_dir: Path) -> None:
        catalog = load_all_scenarios(scenarios_dir)
        for sid in catalog:
            parts = sid.split("-")
            assert len(parts) == 2, f"Bad ID format: {sid}"
            assert parts[0] in ("L1", "L2", "L3"), f"Bad level prefix: {sid}"
            assert parts[1].isdigit() and len(parts[1]) == 3, f"Bad number: {sid}"

    def test_level_matches_id_prefix(self, scenarios_dir: Path) -> None:
        catalog = load_all_scenarios(scenarios_dir)
        for sid, s in catalog.items():
            prefix = sid.split("-")[0]
            assert s.level.value == prefix, f"{sid}: level {s.level} != prefix {prefix}"


class TestGetScenario:
    def test_get_existing(self, scenarios_dir: Path) -> None:
        s = get_scenario("L1-001", scenarios_dir)
        assert isinstance(s, ScenarioDefinition)
        assert s.id == "L1-001"

    def test_get_nonexistent(self, scenarios_dir: Path) -> None:
        with pytest.raises(KeyError, match="L9-999"):
            get_scenario("L9-999", scenarios_dir)


class TestListScenarios:
    def test_list_all(self, scenarios_dir: Path) -> None:
        all_scenarios = list_scenarios(scenarios_dir=scenarios_dir)
        assert len(all_scenarios) == 40

    def test_list_by_level(self, scenarios_dir: Path) -> None:
        l1 = list_scenarios(level="L1", scenarios_dir=scenarios_dir)
        assert all(s.level == Level.L1 for s in l1)
        assert len(l1) == 13

    def test_list_sorted_by_id(self, scenarios_dir: Path) -> None:
        scenarios = list_scenarios(scenarios_dir=scenarios_dir)
        ids = [s.id for s in scenarios]
        assert ids == sorted(ids)


class TestIndividualYamlFiles:
    @pytest.mark.parametrize(
        "filename,expected_count",
        [
            ("L1_compute.yaml", 10),
            ("L1_storage.yaml", 3),
            ("L2_compute.yaml", 7),
            ("L2_data_pipeline.yaml", 4),
            ("L3_network.yaml", 6),
            ("L3_multi_account.yaml", 4),
            ("L3_data_arch.yaml", 6),
        ],
    )
    def test_file_scenario_count(
        self, scenarios_dir: Path, filename: str, expected_count: int
    ) -> None:
        path = scenarios_dir / filename
        assert path.exists(), f"Missing file: {filename}"
        scenarios = load_scenario_file(path)
        assert len(scenarios) == expected_count, (
            f"{filename}: expected {expected_count}, got {len(scenarios)}"
        )
