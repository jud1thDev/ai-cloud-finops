"""Generate a scenario README.md with company background context."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from finops_sim.company.profile import CompanyProfile
from finops_sim.generators.base import GenerationContext


class ReadmeGenerator:
    """Generates a README.md that sets the scene for the FinOps problem."""

    def __init__(self, ctx: GenerationContext, company: CompanyProfile) -> None:
        self.ctx = ctx
        self.company = company

    def generate(self) -> str:
        s = self.ctx.scenario
        c = self.company

        lines = [
            "# FinOps 시뮬레이션 시나리오",
            "",
            "## 회사 정보",
            "",
            "| 항목 | 내용 |",
            "|------|------|",
            "| 회사명 | %s |" % c.name,
            "| 업종 | %s |" % c.industry,
            "| 직원 수 | %d명 |" % c.employee_count,
            "| 성장 단계 | %s |" % c.growth_stage,
            "| 클라우드 성숙도 | %s |" % c.cloud_maturity,
            "| FinOps 전담팀 | %s |" % ("있음" if c.has_finops_team else "없음"),
            "| 월 클라우드 비용 | $%s |" % "{:,.2f}".format(c.monthly_cloud_spend_usd),
            "",
            "## 배경",
            "",
            "%s" % c.stage_description,
            "",
            "최근 클라우드 비용이 예상보다 빠르게 증가하고 있어, 인프라 전반의 비용 최적화 검토를 요청받았습니다.",
            "",
            "## 과제",
            "",
            "아래 제공된 자료를 분석하여 비용 낭비 요소를 찾고, 구체적인 개선 방안과 예상 절감액을 제시하세요.",
            "",
            "### 제공 자료",
            "",
            "1. **Terraform 설정** (`main.tf`) — 현재 인프라 구성",
            "2. **메트릭 데이터** (`metrics/metrics.json`) — 30일간 CloudWatch 메트릭",
            "3. **비용 리포트** (`cost_report.json`) — 6개월 비용 히스토리",
            "",
            "### 기대 산출물",
            "",
            "1. 발견된 비용 문제와 근거",
            "2. 근본 원인 분석",
            "3. 구체적인 해결 방안",
            "4. 월간 예상 절감액",
            "",
            "---",
            "",
            "| 난이도 | 관련 서비스 | 카테고리 |",
            "|--------|-----------|----------|",
            "| %s | %s | %s |" % (s.level.value, ", ".join(s.aws_services), s.category),
            "",
        ]

        return "\n".join(lines)

    def write(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / "README.md"
        out_path.write_text(self.generate(), encoding="utf-8")
        return out_path
