"""Tests for CURReportGenerator."""

from __future__ import annotations

import csv
import io
from pathlib import Path

import pytest

from finops_sim.generators.orchestrator import generate_fixed


EXPECTED_HEADERS = [
    "identity/LineItemId",
    "identity/TimeInterval",
    "lineItem/UsageStartDate",
    "lineItem/UsageEndDate",
    "lineItem/ProductCode",
    "lineItem/UsageType",
    "lineItem/Operation",
    "lineItem/UsageAmount",
    "lineItem/UnblendedCost",
    "lineItem/BlendedCost",
    "lineItem/LineItemType",
    "product/region",
    "resourceTags/user:Service",
    "resourceTags/user:Team",
    "resourceTags/user:Env",
]


@pytest.fixture
def cur_output(tmp_path):
    result = generate_fixed(
        "L1-001",
        str(tmp_path),
        seed=42,
        generators_override={"cur_report"},
    )
    return result, tmp_path


class TestCURReport:
    def test_file_created(self, cur_output):
        result, _ = cur_output
        assert "cur_report" in result["files"]
        assert Path(result["files"]["cur_report"]).exists()

    def test_csv_parseable(self, cur_output):
        result, _ = cur_output
        content = Path(result["files"]["cur_report"]).read_text()
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) > 0

    def test_standard_headers(self, cur_output):
        result, _ = cur_output
        content = Path(result["files"]["cur_report"]).read_text()
        reader = csv.DictReader(io.StringIO(content))
        assert set(EXPECTED_HEADERS).issubset(set(reader.fieldnames))

    def test_has_30_days_of_data(self, cur_output):
        result, _ = cur_output
        content = Path(result["files"]["cur_report"]).read_text()
        reader = csv.DictReader(io.StringIO(content))
        dates = set()
        for row in reader:
            dates.add(row["lineItem/UsageStartDate"][:10])
        assert len(dates) == 30

    def test_costs_are_numeric(self, cur_output):
        result, _ = cur_output
        content = Path(result["files"]["cur_report"]).read_text()
        reader = csv.DictReader(io.StringIO(content))
        for row in reader:
            cost = float(row["lineItem/UnblendedCost"])
            assert cost >= 0
