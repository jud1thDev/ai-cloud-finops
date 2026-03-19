"""Tests for company profile generation."""

from __future__ import annotations

from finops_sim.company.profile import CompanyProfile, generate_company_profile


class TestCompanyProfile:
    def test_generates_profile(self) -> None:
        profile = generate_company_profile(seed=42)
        assert isinstance(profile, CompanyProfile)
        assert profile.name
        assert profile.industry
        assert profile.employee_count > 0
        assert profile.monthly_cloud_spend_usd > 0

    def test_reproducible(self) -> None:
        p1 = generate_company_profile(seed=99)
        p2 = generate_company_profile(seed=99)
        assert p1.name == p2.name
        assert p1.industry == p2.industry
        assert p1.employee_count == p2.employee_count

    def test_different_seeds_differ(self) -> None:
        p1 = generate_company_profile(seed=1)
        p2 = generate_company_profile(seed=2)
        # At least one field should differ (overwhelmingly likely)
        assert (
            p1.name != p2.name
            or p1.industry != p2.industry
            or p1.employee_count != p2.employee_count
        )

    def test_to_dict(self) -> None:
        profile = generate_company_profile(seed=42)
        d = profile.to_dict()
        assert "company_name" in d
        assert "industry" in d
        assert "monthly_cloud_spend_usd" in d
        assert isinstance(d["typical_services"], list)
