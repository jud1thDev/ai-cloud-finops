"""Passthrough (no-LLM) fallback that uses template-based generation."""

from __future__ import annotations

from typing import Any, Dict


class PassthroughLLM:
    """Fallback when no LLM API key is available.

    Returns template-based text without any API calls.
    """

    def generate_company_story(
        self,
        company_profile: Dict[str, Any],
        scenario_title: str,
        scenario_description: str,
    ) -> str:
        name = company_profile.get("company_name", "회사")
        industry = company_profile.get("industry", "IT")
        employees = company_profile.get("employee_count", 50)
        stage = company_profile.get("growth_stage", "성장기")
        spend = company_profile.get("monthly_cloud_spend_usd", 10000)

        return (
            "{name}은(는) {industry} 분야의 {stage} 기업으로, "
            "직원 {employees}명이 근무하고 있습니다. "
            "월 클라우드 비용은 약 ${spend:,.0f}이며, "
            "최근 비용 증가가 눈에 띄어 인프라 전반의 비용 검토를 시작했습니다. "
            "이번 검토에서 특히 주목할 영역은 '{title}' 관련 설정입니다."
        ).format(
            name=name,
            industry=industry,
            stage=stage,
            employees=employees,
            spend=spend,
            title=scenario_title,
        )

    def enrich_readme(
        self,
        base_readme: str,
        company_profile: Dict[str, Any],
    ) -> str:
        story = self.generate_company_story(
            company_profile,
            scenario_title="클라우드 비용 최적화",
            scenario_description="",
        )
        # Insert story after the "## 배경" section
        marker = "## 배경"
        if marker in base_readme:
            parts = base_readme.split(marker, 1)
            return parts[0] + marker + "\n\n" + story + "\n" + parts[1]
        return base_readme + "\n\n" + story

    def generate_hint(
        self,
        scenario_title: str,
        scenario_category: str,
        level: str,
    ) -> str:
        category_hints = {
            "unused": "사용되지 않는 리소스가 비용을 발생시키고 있을 수 있습니다.",
            "overprovisioning": "일부 리소스가 실제 사용량 대비 과도하게 프로비저닝되어 있을 수 있습니다.",
            "rate": "요금 모델이나 할인 적용에 개선 여지가 있을 수 있습니다.",
            "network": "네트워크 아키텍처의 데이터 전송 비용을 점검해 보세요.",
            "tagging": "리소스 태깅과 비용 할당 체계를 확인해 보세요.",
            "data": "데이터 처리 및 저장 아키텍처의 비용 효율성을 검토해 보세요.",
            "architecture": "전체 아키텍처 관점에서 비용 최적화 기회를 찾아보세요.",
            "anomaly": "비용 패턴에서 비정상적인 변화가 있는지 확인해 보세요.",
        }
        return category_hints.get(
            scenario_category,
            "인프라 설정에서 비용 최적화 기회를 찾아보세요.",
        )
