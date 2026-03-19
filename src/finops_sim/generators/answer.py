"""Generate answer.json and scoring_rubric.json from a scenario definition."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from finops_sim.generators.base import GenerationContext


class AnswerGenerator:
    """Builds reference answer and scoring rubric files for a scenario."""

    def __init__(self, ctx: GenerationContext) -> None:
        self.ctx = ctx

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_answer(self) -> Dict[str, Any]:
        """Return the full answer dict for the scenario."""
        scenario = self.ctx.scenario
        answer = scenario.answer
        monthly = answer.savings_estimate_monthly_usd

        affected: List[Dict[str, Any]] = []
        if self.ctx.manifest is not None:
            for res in self.ctx.manifest.problem_resources:
                affected.append(
                    {
                        "resource_name": res.resource_name,
                        "resource_type": res.resource_type,
                        "why_problem": self._why_problem(res.config),
                    }
                )

        return {
            "scenario_id": scenario.id,
            "title": scenario.title,
            "level": scenario.level.value,
            "severity": answer.severity,
            "problem_summary": answer.problem_summary,
            "root_cause": scenario.description,
            "recommendation": answer.recommendation,
            "savings_estimate": {
                "monthly_usd": monthly,
                "annual_usd": round(monthly * 12, 2),
            },
            "affected_resources": affected,
            "evidence_pointers": list(answer.evidence_pointers),
            "detection_method": scenario.detection_method,
        }

    def generate_scoring_rubric(self) -> Dict[str, Any]:
        """Return the scoring rubric dict for the scenario."""
        scenario = self.ctx.scenario
        scoring = scenario.scoring
        answer = self.generate_answer()

        return {
            "scenario_id": scenario.id,
            "total_points": scoring.total,
            "rubric": {
                "identify_problem": {
                    "points": scoring.identify_problem,
                    "description": "Correctly identify the cost problem",
                },
                "identify_root_cause": {
                    "points": scoring.identify_root_cause,
                    "description": "Identify the root cause of the waste",
                },
                "propose_solution": {
                    "points": scoring.propose_solution,
                    "description": "Propose an actionable solution",
                },
                "estimate_savings": {
                    "points": scoring.estimate_savings,
                    "description": "Provide a reasonable savings estimate",
                },
            },
            "reference_answer_summary": answer["problem_summary"],
        }

    def write(self, output_dir: Path) -> Tuple[Path, Path]:
        """Write answer.json and scoring_rubric.json to *output_dir*.

        Returns a tuple of ``(answer_path, rubric_path)``.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        answer_path = output_dir / "answer.json"
        rubric_path = output_dir / "scoring_rubric.json"

        answer_path.write_text(
            json.dumps(self.generate_answer(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        rubric_path.write_text(
            json.dumps(self.generate_scoring_rubric(), indent=2, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )

        return answer_path, rubric_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _why_problem(config: Dict[str, Any]) -> str:
        """Derive a human-readable reason string from a resource config dict.

        Example output: ``"state=stopped, stop_age_days=45"``
        """
        if not config:
            return ""
        parts = [f"{k}={v}" for k, v in config.items()]
        return ", ".join(parts)
