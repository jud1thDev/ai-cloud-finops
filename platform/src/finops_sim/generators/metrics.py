"""Generate 30-day time series metric JSON files from scenario definitions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from finops_sim.config import METRICS_DAYS, METRICS_POINTS_PER_DAY
from finops_sim.generators.base import GenerationContext, MetricsProfile
from finops_sim.utils.random_helpers import SeededRandom


class MetricsGenerator:
    """Generates realistic CloudWatch-style metrics for each resource instance."""

    def __init__(self, ctx: GenerationContext) -> None:
        self.ctx = ctx
        self.rng = SeededRandom(ctx.seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self) -> dict[str, Any]:
        """Build the full metrics payload for every resource in the manifest.

        Returns a dict ready to be serialised as JSON.
        """
        scenario = self.ctx.scenario
        manifest = self.ctx.manifest
        total_points = METRICS_DAYS * METRICS_POINTS_PER_DAY

        resources_out: dict[str, Any] = {}

        for idx, instance in enumerate(manifest.instances):
            # Pick the right profile list based on problem/decoy status.
            profile_key = (
                "problem_resources" if instance.is_problem else "decoy_resources"
            )
            profiles: list[MetricsProfile] = scenario.metrics_profile.get(
                profile_key, []
            )

            # Create a per-resource sub-RNG so each resource gets unique but
            # reproducible variation without disturbing the global sequence.
            sub_rng = SeededRandom(self.ctx.seed + idx + 1)

            metrics_out: dict[str, Any] = {}
            for profile in profiles:
                # Apply slight per-resource variation to numeric params.
                varied_params = self._vary_params(profile.params, sub_rng)

                datapoints = sub_rng.timeseries(
                    length=total_points,
                    pattern=profile.pattern_type,
                    **varied_params,
                )

                metrics_out[profile.metric_name] = {
                    "unit": self._infer_unit(profile.metric_name),
                    "datapoints": datapoints,
                }

            resources_out[instance.resource_name] = {
                "resource_type": instance.resource_type,
                "is_problem": instance.is_problem,
                "metrics": metrics_out,
            }

        return {
            "metadata": {
                "scenario_id": scenario.id,
                "period_days": METRICS_DAYS,
                "resolution": "hourly",
                "points_per_series": total_points,
                "generated_seed": self.ctx.seed,
            },
            "resources": resources_out,
        }

    def write(self, output_dir: Path) -> Path:
        """Write the metrics JSON to *output_dir*/metrics/metrics.json.

        Creates the ``metrics/`` sub-directory if it does not exist and
        returns the path to the written file.
        """
        data = self.generate()
        metrics_dir = output_dir / "metrics"
        metrics_dir.mkdir(parents=True, exist_ok=True)
        out_path = metrics_dir / "metrics.json"
        out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return out_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _infer_unit(self, metric_name: str) -> str:
        """Infer a CloudWatch-style unit string from a metric name suffix."""
        name = metric_name.lower()

        if name.endswith("_percent") or name.endswith("_pct"):
            return "Percent"
        if name.endswith(("_bytes", "_gb", "_mb")):
            return "Bytes"
        if name.endswith(("_count", "_connections")):
            return "Count"
        if name.endswith(("_ms", "_duration")):
            return "Milliseconds"
        if name.endswith("_iops"):
            return "Count/Second"
        return "None"

    @staticmethod
    def _vary_params(params: dict[str, Any], rng: SeededRandom) -> dict[str, Any]:
        """Return a shallow copy of *params* with slight numeric jitter.

        Non-numeric values are passed through unchanged.  The jitter is
        +/- 5 % of the original value, which is enough to make each
        resource visually distinct while preserving the intended pattern.
        """
        varied: dict[str, Any] = {}
        for key, value in params.items():
            if isinstance(value, (int, float)):
                jitter = rng.floating(-0.05, 0.05)
                varied[key] = round(value * (1.0 + jitter), 4)
            else:
                varied[key] = value
        return varied
