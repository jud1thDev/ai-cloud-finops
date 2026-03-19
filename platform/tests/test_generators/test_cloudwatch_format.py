"""Tests for CloudWatchFormatGenerator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from finops_sim.generators.orchestrator import generate_fixed


@pytest.fixture
def cw_output(tmp_path):
    result = generate_fixed(
        "L1-001",
        str(tmp_path),
        seed=42,
        generators_override={"cloudwatch_format"},
    )
    return result, tmp_path


class TestCloudWatchFormat:
    def test_file_created(self, cw_output):
        result, _ = cw_output
        assert "cloudwatch_format" in result["files"]
        assert Path(result["files"]["cloudwatch_format"]).exists()

    def test_has_metric_data_results(self, cw_output):
        result, _ = cw_output
        data = json.loads(Path(result["files"]["cloudwatch_format"]).read_text())
        assert "MetricDataResults" in data
        assert isinstance(data["MetricDataResults"], list)
        assert len(data["MetricDataResults"]) > 0

    def test_result_structure(self, cw_output):
        result, _ = cw_output
        data = json.loads(Path(result["files"]["cloudwatch_format"]).read_text())
        for item in data["MetricDataResults"]:
            assert "Id" in item
            assert "Label" in item
            assert "Timestamps" in item
            assert "Values" in item
            assert "StatusCode" in item
            assert item["StatusCode"] == "Complete"

    def test_timestamps_are_iso8601(self, cw_output):
        result, _ = cw_output
        data = json.loads(Path(result["files"]["cloudwatch_format"]).read_text())
        item = data["MetricDataResults"][0]
        assert len(item["Timestamps"]) == 720  # 30 days × 24 hours
        # Check ISO 8601 format
        ts = item["Timestamps"][0]
        assert ts.endswith("Z")
        assert "T" in ts

    def test_values_match_timestamps(self, cw_output):
        result, _ = cw_output
        data = json.loads(Path(result["files"]["cloudwatch_format"]).read_text())
        for item in data["MetricDataResults"]:
            assert len(item["Values"]) == len(item["Timestamps"])
