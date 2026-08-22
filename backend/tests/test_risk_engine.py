"""
Unit tests for deterministic multi-factor Risk Engine scoring and priority rules.
"""
from app.risk.engine import RiskEngine
from app.risk.scoring import calculate_raw_score, calculate_risk_score, determine_risk_level
from app.risk.factors import (
    get_exploitability_weight, get_exposure_weight,
    get_asset_criticality_weight, get_confidence_weight
)


def test_severity_baseline_scoring():
    # CRITICAL finding baseline with UNKNOWN context should be in CRITICAL range (>= 80)
    res_crit = RiskEngine.evaluate(
        type="DEPENDENCY",
        severity="CRITICAL",
        title="Critical Vulnerability",
        exposure="UNKNOWN",
        asset_criticality="UNKNOWN"
    )
    assert res_crit.risk_score >= 80
    assert res_crit.risk_level == "CRITICAL"
    assert res_crit.priority in ("P0", "P1")

    # HIGH finding baseline with UNKNOWN context should be in HIGH range (>= 60)
    res_high = RiskEngine.evaluate(
        type="DEPENDENCY",
        severity="HIGH",
        title="High Vulnerability",
        exposure="UNKNOWN",
        asset_criticality="UNKNOWN"
    )
    assert res_high.risk_score >= 60
    assert res_high.risk_level == "HIGH"
    assert res_high.priority in ("P1", "P2")


def test_critical_vulnerability_never_downgraded_to_low():
    # Even under low contextual multipliers, a CRITICAL finding must remain in HIGH/CRITICAL range
    res = RiskEngine.evaluate(
        type="DEPENDENCY",
        severity="CRITICAL",
        title="Critical CVE",
        exposure="LOCAL",
        asset_criticality="LOW"
    )
    assert res.risk_score >= 60
    assert res.risk_level != "LOW"
    assert res.risk_score > 34


def test_unknown_context_explanation_and_neutral_factors():
    res = RiskEngine.evaluate(
        type="DEPENDENCY",
        severity="HIGH",
        title="Test Vuln",
        exposure="UNKNOWN",
        asset_criticality="UNKNOWN"
    )
    assert "UNKNOWN" in res.explanation
    assert res.exposure_factor == 1.00
    assert res.asset_criticality_factor == 1.00


def test_100_iteration_determinism():
    first_res = RiskEngine.evaluate(
        type="SECRET",
        severity="CRITICAL",
        title="AWS Key Leak",
        file_path=".env",
        scanner="gitleaks",
        exposure="INTERNET",
        asset_criticality="CRITICAL"
    )

    for _ in range(100):
        res = RiskEngine.evaluate(
            type="SECRET",
            severity="CRITICAL",
            title="AWS Key Leak",
            file_path=".env",
            scanner="gitleaks",
            exposure="INTERNET",
            asset_criticality="CRITICAL"
        )
        assert res.risk_score == first_res.risk_score
        assert res.risk_level == first_res.risk_level
        assert res.priority == first_res.priority
        assert res.explanation == first_res.explanation
