import math
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


# Severity weights used by the aggregate security score formula.
# Higher weight = finding contributes more to overall risk.
_SCORE_SEVERITY_WEIGHTS: Dict[str, float] = {
    "CRITICAL": 4.0,
    "HIGH": 2.0,
    "MEDIUM": 1.0,
    "LOW": 0.3,
    "INFO": 0.0,
}

# Logarithmic scale factor. Larger = gentler slope (more lenient at high
# finding counts). Chosen so that single-finding scores match the previous
# linear formula numerically: 1 HIGH → 87, 1 CRITICAL → 70.
_SCORE_SCALE: float = 10.0


def calculate_security_score(finding_assessments: list) -> int:
    """
    Computes an overall 0–100 Security Score from active open findings'
    risk assessments. 100 = Clean / No active risks detected.

    Uses logarithmic (diminishing-returns) aggregation:

        weighted_sum = Σ( severity_weight × risk_score / 100 )
        penalty      = 100 × ( 1 − e^(−weighted_sum / SCALE) )
        score        = round( 100 − penalty )   [clamped 0–100]

    Severity weights: CRITICAL=4.0, HIGH=2.0, MEDIUM=1.0, LOW=0.3, INFO=0.0
    Scale (SCALE=10): preserves single-finding scores from the previous
    formula while preventing score collapse at higher finding counts.

    Properties:
        • 0 findings          → 100 (perfect)
        • 1 HIGH  (risk=68)  →  87 (Good)
        • 1 CRIT  (risk=90)  →  70 (Needs Attention)
        • 8 HIGH  findings   →  34 (High Risk, not 0)
        • 25 HIGH findings   →   3 (Critical Risk)
        • Score approaches 0 only at extreme finding counts (≥50 HIGH)
        • Score never goes below 0, never above 100
    """
    if not finding_assessments:
        return 100

    weighted_sum = 0.0
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

        weight = _SCORE_SEVERITY_WEIGHTS.get(sev, 0.0)
        weighted_sum += weight * (r_score / 100.0)

    penalty = 100.0 * (1.0 - math.exp(-weighted_sum / _SCORE_SCALE))
    score = 100.0 - penalty
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

