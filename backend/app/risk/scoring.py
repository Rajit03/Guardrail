from typing import Dict

RISK_THRESHOLDS: Dict[str, int] = {
    "CRITICAL": 80,
    "HIGH": 60,
    "MEDIUM": 35,
    "LOW": 1,
    "INFO": 0,
}

BASE_SEVERITY_SCORES: Dict[str, float] = {
    "CRITICAL": 85.0,
    "HIGH": 65.0,
    "MEDIUM": 45.0,
    "LOW": 20.0,
    "INFO": 0.0,
}


def calculate_raw_score(
    severity_score: float,
    exploitability_factor: float,
    exposure_factor: float,
    asset_criticality_factor: float,
    confidence_factor: float,
) -> float:
    """
    Calculates raw risk score deterministically based on severity baseline and context multiplier.
    Severity sets base score: CRITICAL=85, HIGH=65, MEDIUM=45, LOW=20, INFO=0.
    Context multiplier adjusts base score by average factor weight (range ~0.85 to 1.15).
    """
    context_multiplier = (
        exploitability_factor + exposure_factor + asset_criticality_factor + confidence_factor
    ) / 4.0

    raw = severity_score * context_multiplier
    return max(0.0, min(100.0, raw))


def calculate_risk_score(raw_score: float) -> int:
    """
    Normalizes raw_score to a 0–100 integer range.
    """
    normalized = round(raw_score)
    return max(0, min(100, normalized))


def determine_risk_level(risk_score: int) -> str:
    """
    Maps integer risk_score (0–100) to deterministic risk level:
    80–100 -> CRITICAL
    60–79  -> HIGH
    35–59  -> MEDIUM
    1–34   -> LOW
    0      -> INFO
    """
    score = max(0, min(100, risk_score))
    if score >= RISK_THRESHOLDS["CRITICAL"]:
        return "CRITICAL"
    elif score >= RISK_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif score >= RISK_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    elif score >= RISK_THRESHOLDS["LOW"]:
        return "LOW"
    else:
        return "INFO"


def calculate_security_score(finding_assessments: list) -> int:
    """
    Computes an overall 0–100 Security Score from active open findings' risk assessments.
    100 = Clean / No active risks detected.
    Penalties are proportional to finding severity and risk scores derived from the Risk Engine.
    """
    if not finding_assessments:
        return 100

    total_penalty = 0.0
    for item in finding_assessments:
        # Handle dict, RiskAssessment object, or (severity, risk_score) tuple
        if isinstance(item, tuple):
            sev, r_score = item
        elif isinstance(item, dict):
            sev = item.get("severity", "MEDIUM")
            r_score = item.get("risk_score", 45)
        else:
            sev = getattr(item, "severity", None)
            if not sev and hasattr(item, "finding"):
                sev = getattr(item.finding, "severity", "MEDIUM")
            r_score = getattr(item, "risk_score", 45)

        sev = (sev or "MEDIUM").upper()
        r_score = r_score if r_score is not None else 45

        if sev == "CRITICAL":
            penalty = 18.0 + (r_score * 0.12)
        elif sev == "HIGH":
            penalty = 8.0 + (r_score * 0.08)
        elif sev == "MEDIUM":
            penalty = 3.0 + (r_score * 0.04)
        elif sev == "LOW":
            penalty = 0.5 + (r_score * 0.02)
        else:
            penalty = 0.0

        total_penalty += penalty

    score = max(0.0, 100.0 - total_penalty)
    return max(0, min(100, round(score)))


def determine_security_rating(security_score: int) -> dict:
    """
    Interprets a 0–100 Security Score into human-friendly rating and risk classification:
    90–100: Excellent (LOW risk)
    75–89:  Good (LOW risk)
    50–74:  Needs Attention (MEDIUM risk)
    25–49:  High Risk (HIGH risk)
    0–24:   Critical Risk (CRITICAL risk)
    """
    score = max(0, min(100, security_score))
    if score >= 90:
        return {"rating": "Excellent", "risk_level": "LOW", "status_code": "EXCELLENT"}
    elif score >= 75:
        return {"rating": "Good", "risk_level": "LOW", "status_code": "GOOD"}
    elif score >= 50:
        return {"rating": "Needs Attention", "risk_level": "MEDIUM", "status_code": "NEEDS_ATTENTION"}
    elif score >= 25:
        return {"rating": "High Risk", "risk_level": "HIGH", "status_code": "HIGH_RISK"}
    else:
        return {"rating": "Critical Risk", "risk_level": "CRITICAL", "status_code": "CRITICAL_RISK"}

