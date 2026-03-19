"""Claude API implementation of LLMInterface."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


def _get_client():
    """Lazy-import and instantiate the Anthropic client."""
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "anthropic package not installed. "
            "Install with: pip install 'finops-sim[llm]'"
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY environment variable not set. "
            "Set it to use Claude LLM features."
        )
    return anthropic.Anthropic(api_key=api_key)


class ClaudeLLM:
    """Claude API backend for enriching scenario generation."""

    def __init__(self, model: str = "claude-sonnet-4-20250514") -> None:
        self.model = model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = _get_client()
        return self._client

    def _call(self, system: str, user: str, max_tokens: int = 1024) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": user}],
            system=system,
        )
        return response.content[0].text

    def generate_company_story(
        self,
        company_profile: Dict[str, Any],
        scenario_title: str,
        scenario_description: str,
    ) -> str:
        system = (
            "당신은 FinOps 시뮬레이션을 위한 가상 회사 배경 스토리 작성자입니다. "
            "현실적이고 구체적인 회사 상황을 한국어로 작성하세요. "
            "3-5문장으로 간결하게 작성하고, 비용 문제의 힌트를 주지 마세요."
        )
        user = (
            "다음 회사 프로필로 가상의 배경 스토리를 작성해주세요.\n\n"
            "회사명: {name}\n"
            "업종: {industry}\n"
            "직원수: {employees}명\n"
            "성장단계: {stage}\n"
            "월 클라우드 비용: ${spend:,.0f}\n"
            "주요 서비스: {services}\n\n"
            "이 회사는 현재 '{title}' 관련 인프라를 운영 중입니다."
        ).format(
            name=company_profile.get("company_name", "회사"),
            industry=company_profile.get("industry", "IT"),
            employees=company_profile.get("employee_count", 50),
            stage=company_profile.get("growth_stage", "성장기"),
            spend=company_profile.get("monthly_cloud_spend_usd", 10000),
            services=", ".join(company_profile.get("typical_services", [])),
            title=scenario_title,
        )
        return self._call(system, user, max_tokens=512)

    def enrich_readme(
        self,
        base_readme: str,
        company_profile: Dict[str, Any],
    ) -> str:
        system = (
            "당신은 FinOps 시뮬레이션 문제의 README를 개선하는 전문가입니다. "
            "기존 README의 구조를 유지하면서 회사 배경 섹션을 더 자연스럽고 "
            "현실적으로 다듬어주세요. 정답 힌트는 절대 포함하지 마세요. "
            "마크다운 형식을 유지하세요."
        )
        user = (
            "다음 README를 개선해주세요. 구조는 유지하되, "
            "배경 설명을 더 자연스럽게 만들어주세요.\n\n"
            "---\n{readme}\n---"
        ).format(readme=base_readme)
        return self._call(system, user, max_tokens=2048)

    def generate_hint(
        self,
        scenario_title: str,
        scenario_category: str,
        level: str,
    ) -> str:
        system = (
            "당신은 FinOps 교육 전문가입니다. "
            "학습자에게 정답을 직접 알려주지 않으면서 "
            "올바른 방향으로 사고를 유도하는 힌트를 작성하세요. "
            "1-2문장으로 간결하게 작성하세요."
        )
        user = (
            "난이도: {level}\n"
            "카테고리: {category}\n"
            "시나리오: {title}\n\n"
            "이 문제를 풀기 위한 사고 방향 힌트를 주세요."
        ).format(level=level, category=scenario_category, title=scenario_title)
        return self._call(system, user, max_tokens=256)
