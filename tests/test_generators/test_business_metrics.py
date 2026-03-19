"""Tests for BusinessMetricsGenerator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from finops_sim.generators.orchestrator import generate_fixed


@pytest.fixture
def l2_output(tmp_path):
    """Generate an L2 scenario with business_metrics enabled."""
    result = generate_fixed(
        "L2-014",
        str(tmp_path),
        seed=42,
        generators_override={"business_metrics"},
    )
    return result, tmp_path


class TestBusinessMetrics:
    def test_file_created(self, l2_output):
        result, tmp_path = l2_output
        assert "business_metrics" in result["files"]
        bm_path = Path(result["files"]["business_metrics"])
        assert bm_path.exists()

    def test_daily_metrics_length(self, l2_output):
        result, _ = l2_output
        data = json.loads(Path(result["files"]["business_metrics"]).read_text())
        assert len(data["daily_metrics"]) == 30

    def test_unit_economics_present(self, l2_output):
        result, _ = l2_output
        data = json.loads(Path(result["files"]["business_metrics"]).read_text())
        ue = data["current_unit_economics"]
        assert "cost_per_order" in ue
        assert "cost_per_1k_requests" in ue
        assert "cost_to_revenue_pct" in ue
        assert ue["cost_per_order"] > 0
        assert ue["cost_per_1k_requests"] > 0

    def test_daily_metrics_have_required_fields(self, l2_output):
        result, _ = l2_output
        data = json.loads(Path(result["files"]["business_metrics"]).read_text())
        for day in data["daily_metrics"]:
            assert "date" in day
            assert "requests" in day
            assert "orders" in day
            assert "data_processed_gb" in day
            assert day["requests"] >= 0
            assert day["orders"] >= 1

    def test_reproducible(self, tmp_path):
        r1 = generate_fixed("L2-014", str(tmp_path / "a"), seed=99, generators_override={"business_metrics"})
        r2 = generate_fixed("L2-014", str(tmp_path / "b"), seed=99, generators_override={"business_metrics"})
        d1 = json.loads(Path(r1["files"]["business_metrics"]).read_text())
        d2 = json.loads(Path(r2["files"]["business_metrics"]).read_text())
        assert d1["daily_metrics"] == d2["daily_metrics"]
