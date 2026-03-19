"""Convert metrics to AWS GetMetricData response format for L3 scenarios."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from finops_sim.config import METRICS_DAYS, METRICS_POINTS_PER_DAY
from finops_sim.generators.base import GenerationContext
from finops_sim.generators.metrics import MetricsGenerator


class CloudWatchFormatGenerator:
    """Adapter: wraps MetricsGenerator output into AWS GetMetricData format.

    Produces MetricDataResults[] with ISO 8601 timestamps matching the
    structure returned by cloudwatch:GetMetricData.
    """

    def __init__(self, ctx: GenerationContext) -> None:
        self.ctx = ctx

    def generate(self) -> Dict[str, Any]:
        # Get raw metrics from existing generator
        metrics_gen = MetricsGenerator(self.ctx)
        raw = metrics_gen.generate()

        total_points = METRICS_DAYS * METRICS_POINTS_PER_DAY
        end_time = datetime(2026, 3, 18, 0, 0, 0)
        start_time = end_time - timedelta(days=METRICS_DAYS)

        # Build ISO 8601 timestamp array
        timestamps = [
            (start_time + timedelta(hours=i)).strftime("%Y-%m-%dT%H:%M:%SZ")
            for i in range(total_points)
        ]

        metric_data_results: List[Dict[str, Any]] = []

        for resource_name, resource_data in raw["resources"].items():
            for metric_name, metric_data in resource_data["metrics"].items():
                result_id = f"{resource_name}_{metric_name}".replace("-", "_")
                metric_data_results.append({
                    "Id": result_id,
                    "Label": f"{resource_name}/{metric_name}",
                    "Timestamps": timestamps,
                    "Values": metric_data["datapoints"],
                    "StatusCode": "Complete",
                })

        return {
            "MetricDataResults": metric_data_results,
            "Messages": [],
        }

    def write(self, output_dir: Path) -> Path:
        data = self.generate()
        metrics_dir = output_dir / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        out_path = metrics_dir / "cloudwatch_format.json"
        out_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return out_path
