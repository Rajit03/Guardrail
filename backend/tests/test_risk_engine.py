"""
Unit tests for the Risk Engine.
Verifies severity mappings, factor weights, determinism, and score boundaries.
No external network requests or AI models are used.
"""
import pytest
from app.risk.severity import get_severity_score, SEVERITY_SCORES
from app.risk.factors import (
    get_exploitability_weight,
    get_exposure_weight,
    get_asset_criticality_weight,
    get_confidence_weight,
)
from app.risk.scoring import (
    calculate_raw_score,
    calculate_risk_score,
    determine_risk_level,
)
from app.risk.priority import determine_priority
from app.risk.engine import RiskEngine


# ─── Factor & Mapping Tests ────────────────────────────────────────

def test_severity_mappings():
    assert get_severity_score("CRITICAL") == 10.0
    assert get_severity_score("HIGH") == 8.0
    assert get_severity_score("MEDIUM") == 5.0
    assert get_severity_score("LOW") == 2.0
    assert get_severity_score("INFO") == 0.0
    assert get_severity_score("unknown") == 5.0  # Default fallback


def test_exploitability_mappings():
    assert get_exploitability_weight("VERY_HIGH") == 1.0
    assert get_exploitability_weight("HIGH") == 0.8
    assert get_exploitability_weight("MEDIUM") == 0.5
    assert get_exploitability_weight("LOW") == 0.2
    assert get_exploitability_weight("UNKNOWN") == 0.4
    assert get_exploitability_weight("INVALID") == 0.4


def test_exposure_mappings():
    assert get_exposure_weight("INTERNET") == 1.0
    assert get_exposure_weight("EXTERNAL") == 0.8
    assert get_exposure_weight("INTERNAL") == 0.5
    assert get_exposure_weight("LOCAL") == 0.2
    assert get_exposure_weight("UNKNOWN") == 0.4


def test_asset_criticality_mappings():
    assert get_asset_criticality_weight("CRITICAL") == 1.0
    assert get_asset_criticality_weight("HIGH") == 0.8
    assert get_asset_criticality_weight("MEDIUM") == 0.5
    assert get_asset_criticality_weight("LOW") == 0.2
    assert get_asset_criticality_weight("UNKNOWN") == 0.4


def test_confidence_mappings():
    assert get_confidence_weight("HIGH") == 1.0
    assert get_confidence_weight("MEDIUM") == 0.75
    assert get_confidence_weight("LOW") == 0.5
    assert get_confidence_weight("UNKNOWN") == 0.7


# ─── Boundary Tests ───────────────────────────────────────────────

def test_risk_level_boundaries():
    assert determine_risk_level(0) == "INFO"
    assert determine_risk_level(1) == "LOW"
    assert determine_risk_level(34) == "LOW"
    assert determine_risk_level(35) == "MEDIUM"
    assert determine_risk_level(59) == "MEDIUM"
    assert determine_risk_level(60) == "HIGH"
    assert determine_risk_level(79) == "HIGH"
    assert determine_risk_level(80) == "CRITICAL"
    assert determine_risk_level(100) == "CRITICAL"


def test_risk_score_clamping():
    assert calculate_risk_score(0.0) == 0
    assert calculate_risk_score(10.0) == 100
    assert calculate_risk_score(12.5) == 100
    assert calculate_risk_score(-1.0) == 0


# ─── Priority Assignment Tests ────────────────────────────────────

def test_priority_determination():
    # CRITICAL + INTERNET => P0
    assert determine_priority("CRITICAL", "INTERNET", "HIGH", 80) == "P0"
    # Score >= 80 + EXTERNAL => P0
    assert determine_priority("HIGH", "EXTERNAL", "CRITICAL", 85) == "P0"
    # CRITICAL + UNKNOWN exposure => P1
    assert determine_priority("CRITICAL", "UNKNOWN", "MEDIUM", 65) == "P1"
    # HIGH + EXTERNAL => P1
    assert determine_priority("HIGH", "EXTERNAL", "MEDIUM", 64) == "P1"
    # MEDIUM + INTERNAL => P2
    assert determine_priority("MEDIUM", "INTERNAL", "MEDIUM", 45) == "P2"
    # LOW => P3
    assert determine_priority("LOW", "LOCAL", "LOW", 15) == "P3"


# ─── Determinism Test (100 Iterations) ────────────────────────────

def test_risk_engine_100_percent_determinism():
    """
    Mandatory determinism test:
    Running the same calculation 100 times MUST produce identical results.
    """
    baseline = RiskEngine.evaluate(
        type="SECRET",
        severity="HIGH",
        title="Hardcoded AWS Access Key",
        file_path="config.py",
        scanner="gitleaks",
        rule_id="aws-access-token",
        exposure="INTERNET",
        asset_criticality="HIGH",
        confidence="HIGH"
    )

    for i in range(100):
        run = RiskEngine.evaluate(
            type="SECRET",
            severity="HIGH",
            title="Hardcoded AWS Access Key",
            file_path="config.py",
            scanner="gitleaks",
            rule_id="aws-access-token",
            exposure="INTERNET",
            asset_criticality="HIGH",
            confidence="HIGH"
        )
        assert run.risk_score == baseline.risk_score, f"Iter {i}: score mismatch"
        assert run.risk_level == baseline.risk_level, f"Iter {i}: level mismatch"
        assert run.priority == baseline.priority, f"Iter {i}: priority mismatch"
        assert run.explanation == baseline.explanation, f"Iter {i}: explanation mismatch"
        assert run.recommended_action == baseline.recommended_action, f"Iter {i}: remediation mismatch"
