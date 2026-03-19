"""Core data classes for the generation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Level(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"


@dataclass
class ResourceSpec:
    """Single resource specification from a scenario YAML."""

    type: str  # e.g. "aws_instance"
    config: dict[str, Any] = field(default_factory=dict)
    count: int = 1


@dataclass
class MetricsProfile:
    """Metric generation parameters for a resource group."""

    metric_name: str
    pattern_type: str  # "zero", "normal", "spike", "sawtooth", "step_down", etc.
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class CostProfile:
    """Expected cost impact of a scenario."""

    monthly_waste_usd: float
    services_affected: list[str]
    pricing_note: str = ""


@dataclass
class ScoringRubric:
    """Point allocation for grading a solution."""

    identify_problem: int = 30
    identify_root_cause: int = 20
    propose_solution: int = 30
    estimate_savings: int = 20

    @property
    def total(self) -> int:
        return (
            self.identify_problem
            + self.identify_root_cause
            + self.propose_solution
            + self.estimate_savings
        )


@dataclass
class AnswerSpec:
    """Reference answer for a scenario."""

    severity: str  # "low", "medium", "high", "critical"
    problem_summary: str
    recommendation: str
    savings_estimate_monthly_usd: float
    evidence_pointers: list[str] = field(default_factory=list)


@dataclass
class ScenarioDefinition:
    """Complete parsed scenario from YAML."""

    id: str
    title: str
    category: str
    level: Level
    aws_services: list[str]
    description: str
    detection_method: str
    problem_resources: list[ResourceSpec]
    decoy_resources: list[ResourceSpec]
    metrics_profile: dict[str, list[MetricsProfile]]
    cost_profile: CostProfile
    answer: AnswerSpec
    scoring: ScoringRubric
    tags: list[str] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResourceInstance:
    """A concrete instantiated resource with generated names/IDs."""

    resource_type: str
    resource_name: str  # Terraform resource name
    config: dict[str, Any]
    is_problem: bool
    group_index: int  # index within its resource group


@dataclass
class ResourceManifest:
    """All generated resources for a scenario instance."""

    instances: list[ResourceInstance] = field(default_factory=list)

    @property
    def problem_resources(self) -> list[ResourceInstance]:
        return [r for r in self.instances if r.is_problem]

    @property
    def decoy_resources(self) -> list[ResourceInstance]:
        return [r for r in self.instances if not r.is_problem]


@dataclass
class GenerationContext:
    """Context passed through the entire generation pipeline."""

    scenario: ScenarioDefinition
    seed: int
    output_dir: str
    manifest: ResourceManifest | None = None
    company_name: str = ""
    company_industry: str = ""
