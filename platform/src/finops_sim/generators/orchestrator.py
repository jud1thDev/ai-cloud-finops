"""Orchestrator: coordinates the full generation pipeline for a scenario."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from finops_sim.catalog.loader import get_scenario
from finops_sim.catalog.selector import select_scenarios
from finops_sim.company.profile import CompanyProfile, generate_company_profile
from finops_sim.generators.answer import AnswerGenerator
from finops_sim.generators.base import GenerationContext, Level
from finops_sim.generators.cost_report import CostReportGenerator
from finops_sim.generators.metrics import MetricsGenerator
from finops_sim.generators.readme_gen import ReadmeGenerator
from finops_sim.generators.terraform import TerraformGenerator


def _get_llm(use_llm: bool):
    """Return the appropriate LLM backend."""
    if not use_llm:
        from finops_sim.llm.passthrough import PassthroughLLM
        return PassthroughLLM()

    from finops_sim.llm.claude import ClaudeLLM
    return ClaudeLLM()


def _resolve_generators(scenario, generators_override: Set[str] | None = None) -> Set[str]:
    """Determine which optional generators to activate.

    Priority: explicit override > scenario extras > level-based defaults.
    """
    if generators_override is not None:
        return generators_override

    extras = getattr(scenario, "extras", {}) or {}
    explicit = extras.get("generators")
    if explicit:
        return set(explicit)

    # Level-based defaults
    level = scenario.level
    active: Set[str] = set()

    if level in (Level.L2, Level.L3):
        active.add("business_metrics")
        active.add("tags_inventory")

    if level == Level.L3:
        active.add("cloudwatch_format")
        active.add("cur_report")

    # rate category or ri-sp tag → generate RI/SP data (L2+ only)
    if level in (Level.L2, Level.L3):
        if scenario.category == "rate" or "ri-sp" in (scenario.tags or []):
            active.add("ri_sp_coverage")

    return active


def _generate_one(
    scenario_id: str,
    out: Path,
    seed: int,
    company: CompanyProfile,
    use_llm: bool = False,
    generators_override: Set[str] | None = None,
) -> Dict[str, Any]:
    """Generate all artifacts for a single scenario with a company profile."""
    scenario = get_scenario(scenario_id)
    out.mkdir(parents=True, exist_ok=True)

    ctx = GenerationContext(
        scenario=scenario,
        seed=seed,
        output_dir=str(out),
        company_name=company.name,
        company_industry=company.industry,
    )

    llm = _get_llm(use_llm)

    # 1. Terraform — builds manifest + writes main.tf
    tf_gen = TerraformGenerator(ctx)
    tf_gen.build_manifest()
    tf_path = tf_gen.write(out)

    # 2. Metrics — 30-day time series
    metrics_gen = MetricsGenerator(ctx)
    metrics_path = metrics_gen.write(out)

    # 3. Cost report — 6-month history
    cost_gen = CostReportGenerator(ctx)
    cost_path = cost_gen.write(out)

    # 3.5. Optional generators (between cost_report and answer)
    active_generators = _resolve_generators(scenario, generators_override)
    files: Dict[str, str] = {
        "main_tf": str(tf_path),
        "metrics": str(metrics_path),
        "cost_report": str(cost_path),
    }

    if "business_metrics" in active_generators:
        from finops_sim.generators.business_metrics import BusinessMetricsGenerator
        bm_gen = BusinessMetricsGenerator(ctx)
        bm_path = bm_gen.write(out)
        files["business_metrics"] = str(bm_path)

    if "tags_inventory" in active_generators:
        from finops_sim.generators.tags_inventory import TagsInventoryGenerator
        tags_gen = TagsInventoryGenerator(ctx)
        tags_path = tags_gen.write(out)
        files["tags_inventory"] = str(tags_path)

    if "cloudwatch_format" in active_generators:
        from finops_sim.generators.cloudwatch_format import CloudWatchFormatGenerator
        cw_gen = CloudWatchFormatGenerator(ctx)
        cw_path = cw_gen.write(out)
        files["cloudwatch_format"] = str(cw_path)

    if "cur_report" in active_generators:
        from finops_sim.generators.cur_report import CURReportGenerator
        cur_gen = CURReportGenerator(ctx)
        cur_path = cur_gen.write(out)
        files["cur_report"] = str(cur_path)

    if "ri_sp_coverage" in active_generators:
        from finops_sim.generators.ri_sp_coverage import RISPCoverageGenerator
        risp_gen = RISPCoverageGenerator(ctx)
        risp_path = risp_gen.write(out)
        files["ri_sp_coverage"] = str(risp_path)

    # 4. Answer + scoring rubric
    answer_gen = AnswerGenerator(ctx)
    answer_path, rubric_path = answer_gen.write(out)
    files["answer"] = str(answer_path)
    files["scoring_rubric"] = str(rubric_path)

    # 5. README with company context
    readme_gen = ReadmeGenerator(ctx, company)
    readme_path = readme_gen.write(out)
    files["readme"] = str(readme_path)

    # 6. LLM enrichment — enhance README with natural language
    if use_llm:
        readme_text = readme_path.read_text(encoding="utf-8")
        enriched = llm.enrich_readme(readme_text, company.to_dict())
        readme_path.write_text(enriched, encoding="utf-8")

    # 7. Write hint file
    hint = llm.generate_hint(
        scenario.title, scenario.category, scenario.level.value
    )
    hint_path = out / "hint.txt"
    hint_path.write_text(hint, encoding="utf-8")
    files["hint"] = str(hint_path)

    return {
        "scenario_id": scenario_id,
        "output_dir": str(out),
        "company": company.name,
        "files": files,
        "resource_count": len(ctx.manifest.instances),
        "problem_count": len(ctx.manifest.problem_resources),
        "decoy_count": len(ctx.manifest.decoy_resources),
        "llm_used": use_llm,
        "active_generators": sorted(active_generators),
    }


def generate_fixed(
    scenario_id: str,
    output_dir: str,
    seed: int = 42,
    use_llm: bool = False,
    generators_override: Set[str] | None = None,
) -> Dict[str, Any]:
    """Generate all artifacts for a single fixed scenario."""
    company = generate_company_profile(seed)
    out = Path(output_dir) / scenario_id
    return _generate_one(scenario_id, out, seed, company, use_llm, generators_override)


def generate_auto(
    level: str,
    num_problems: int,
    output_dir: str,
    seed: int = 42,
    category: Optional[str] = None,
    use_llm: bool = False,
    generators_override: Set[str] | None = None,
) -> List[Dict[str, Any]]:
    """Auto-select and generate multiple scenarios."""
    company = generate_company_profile(seed)
    scenarios = select_scenarios(level, num_problems, seed, category)
    base_out = Path(output_dir)

    results: List[Dict[str, Any]] = []
    for i, s in enumerate(scenarios):
        sub_seed = seed + i * 1000
        out = base_out / s.id
        result = _generate_one(s.id, out, sub_seed, company, use_llm, generators_override)
        results.append(result)

    return results
