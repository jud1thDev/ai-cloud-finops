"""Company profile generation for realistic scenario context."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml

from finops_sim.config import COMPANY_TEMPLATES
from finops_sim.utils.random_helpers import SeededRandom


@dataclass
class CompanyProfile:
    """Generated company profile for a scenario."""

    name: str
    industry: str
    industry_en: str
    employee_count: int
    growth_stage: str
    growth_stage_en: str
    cloud_maturity: str
    has_finops_team: bool
    monthly_cloud_spend_usd: float
    typical_services: List[str] = field(default_factory=list)
    stage_description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "company_name": self.name,
            "industry": self.industry,
            "industry_en": self.industry_en,
            "employee_count": self.employee_count,
            "growth_stage": self.growth_stage,
            "growth_stage_en": self.growth_stage_en,
            "cloud_maturity": self.cloud_maturity,
            "has_finops_team": self.has_finops_team,
            "monthly_cloud_spend_usd": self.monthly_cloud_spend_usd,
            "typical_services": self.typical_services,
            "stage_description": self.stage_description,
        }


def _load_templates(path: Path = None) -> Dict[str, Any]:
    p = path or COMPANY_TEMPLATES
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def generate_company_profile(
    seed: int,
    templates_path: Path = None,
) -> CompanyProfile:
    """Generate a random but reproducible company profile."""
    rng = SeededRandom(seed)
    templates = _load_templates(templates_path)

    industry = rng.choice(templates["industries"])
    stage = rng.choice(templates["growth_stages"])

    company_name = rng.choice(industry["company_names"])
    low, high = industry["monthly_spend_range"]
    monthly_spend = round(rng.floating(float(low), float(high)), 2)

    emp_low, emp_high = stage["employee_range"]
    employee_count = rng.integer(emp_low, emp_high)

    return CompanyProfile(
        name=company_name,
        industry=industry["name"],
        industry_en=industry["name_en"],
        employee_count=employee_count,
        growth_stage=stage["name"],
        growth_stage_en=stage["name_en"],
        cloud_maturity=stage["cloud_maturity"],
        has_finops_team=stage["finops_team"],
        monthly_cloud_spend_usd=monthly_spend,
        typical_services=industry["typical_services"],
        stage_description=stage["description"],
    )
