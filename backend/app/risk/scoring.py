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
