"""YAML scenario loader with Pydantic validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from finops_sim.config import SCENARIOS_DIR
from finops_sim.generators.base import (
    AnswerSpec,
    CostProfile,
    Level,
    MetricsProfile,
    ResourceSpec,
    ScenarioDefinition,
    ScoringRubric,
)


# ── Pydantic models for YAML validation ──


class ResourceConfigModel(BaseModel):
    type: str
    config: dict[str, Any] = Field(default_factory=dict)
    count: int = 1


class MetricSpecModel(BaseModel):
    type: str
    mean: float | None = None
    std: float | None = None
    value: float | None = None
    spike_chance: float | None = None
    spike_mult: float | None = None
    period: int | None = None
    low: float | None = None
    high: float | None = None
    step_at: int | None = None


class CostProfileModel(BaseModel):
    monthly_waste_usd: float
    services_affected: list[str]
    pricing_note: str = ""


class AnswerModel(BaseModel):
    severity: str
    problem_summary: str
    recommendation: str
    savings_estimate_monthly_usd: float
    evidence_pointers: list[str] = Field(default_factory=list)

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"low", "medium", "high", "critical"}
        if v not in allowed:
            raise ValueError(f"severity must be one of {allowed}, got {v!r}")
        return v


class ScoringModel(BaseModel):
    identify_problem: int = 30
    identify_root_cause: int = 20
    propose_solution: int = 30
    estimate_savings: int = 20


class ScenarioModel(BaseModel):
    id: str
    title: str
    category: str
    level: str
    aws_services: list[str]
    description: str
    detection_method: str
    resources: dict[str, list[ResourceConfigModel]]
    metrics_profile: dict[str, dict[str, MetricSpecModel]]
    cost_profile: CostProfileModel
    answer: AnswerModel
    scoring: ScoringModel
    tags: list[str] = Field(default_factory=list)
    extras: dict[str, Any] = Field(default_factory=dict)

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        if v not in ("L1", "L2", "L3"):
            raise ValueError(f"level must be L1/L2/L3, got {v!r}")
        return v


class ScenariosFile(BaseModel):
    scenarios: list[ScenarioModel]


# ── Conversion helpers ──


def _to_resource_specs(items: list[ResourceConfigModel]) -> list[ResourceSpec]:
    return [ResourceSpec(type=r.type, config=r.config, count=r.count) for r in items]


def _to_metrics_profiles(
    raw: dict[str, dict[str, MetricSpecModel]],
) -> dict[str, list[MetricsProfile]]:
    result: dict[str, list[MetricsProfile]] = {}
    for group, metrics in raw.items():
        profiles = []
        for metric_name, spec in metrics.items():
            params = {
                k: v
                for k, v in spec.model_dump().items()
                if k != "type" and v is not None
            }
            profiles.append(
                MetricsProfile(
                    metric_name=metric_name,
                    pattern_type=spec.type,
                    params=params,
                )
            )
        result[group] = profiles
    return result


def _to_scenario_def(m: ScenarioModel) -> ScenarioDefinition:
    return ScenarioDefinition(
        id=m.id,
        title=m.title,
        category=m.category,
        level=Level(m.level),
        aws_services=m.aws_services,
        description=m.description,
        detection_method=m.detection_method,
        problem_resources=_to_resource_specs(m.resources.get("problem", [])),
        decoy_resources=_to_resource_specs(m.resources.get("decoy", [])),
        metrics_profile=_to_metrics_profiles(m.metrics_profile),
        cost_profile=CostProfile(
            monthly_waste_usd=m.cost_profile.monthly_waste_usd,
            services_affected=m.cost_profile.services_affected,
            pricing_note=m.cost_profile.pricing_note,
        ),
        answer=AnswerSpec(
            severity=m.answer.severity,
            problem_summary=m.answer.problem_summary,
            recommendation=m.answer.recommendation,
            savings_estimate_monthly_usd=m.answer.savings_estimate_monthly_usd,
            evidence_pointers=m.answer.evidence_pointers,
        ),
        scoring=ScoringRubric(
            identify_problem=m.scoring.identify_problem,
            identify_root_cause=m.scoring.identify_root_cause,
            propose_solution=m.scoring.propose_solution,
            estimate_savings=m.scoring.estimate_savings,
        ),
        tags=m.tags,
        extras=m.extras,
    )


# ── Public API ──


def load_scenario_file(path: Path) -> list[ScenarioDefinition]:
    """Load and validate a single YAML scenario file."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    validated = ScenariosFile.model_validate(raw)
    return [_to_scenario_def(s) for s in validated.scenarios]


def load_all_scenarios(
    scenarios_dir: Path | None = None,
) -> dict[str, ScenarioDefinition]:
    """Load all scenario YAML files. Returns dict keyed by scenario ID."""
    base = scenarios_dir or SCENARIOS_DIR
    catalog: dict[str, ScenarioDefinition] = {}

    for yaml_file in sorted(base.glob("*.yaml")):
        scenarios = load_scenario_file(yaml_file)
        for s in scenarios:
            if s.id in catalog:
                raise ValueError(
                    f"Duplicate scenario ID {s.id!r} in {yaml_file.name}"
                )
            catalog[s.id] = s

    return catalog


def get_scenario(
    scenario_id: str, scenarios_dir: Path | None = None
) -> ScenarioDefinition:
    """Load a specific scenario by ID."""
    catalog = load_all_scenarios(scenarios_dir)
    if scenario_id not in catalog:
        available = ", ".join(sorted(catalog.keys()))
        raise KeyError(
            f"Scenario {scenario_id!r} not found. Available: {available}"
        )
    return catalog[scenario_id]


def list_scenarios(
    level: str | None = None, scenarios_dir: Path | None = None
) -> list[ScenarioDefinition]:
    """List scenarios, optionally filtered by level."""
    catalog = load_all_scenarios(scenarios_dir)
    scenarios = list(catalog.values())
    if level:
        scenarios = [s for s in scenarios if s.level.value == level]
    return sorted(scenarios, key=lambda s: s.id)
