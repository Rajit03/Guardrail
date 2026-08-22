from typing import Dict

RISK_THRESHOLDS: Dict[str, int] = {
    "CRITICAL": 80,
    "HIGH": 60,
    "MEDIUM": 35,
    "LOW": 1,
    "INFO": 0,
}


def calculate_raw_score(
    severity_score: float,
    exploitability_factor: float,
    exposure_factor: float,
    asset_criticality_factor: float,
    confidence_factor: float,
) -> float:
    """
    Calculates raw risk score deterministically via factor multiplication.
    raw_score = severity_score * exploitability * exposure * asset_criticality * confidence
    Maximum possible value is 10.0.
    """
    raw = (
        severity_score
        * exploitability_factor
        * exposure_factor
        * asset_criticality_factor
        * confidence_factor
    )
    return max(0.0, min(10.0, raw))


def calculate_risk_score(raw_score: float) -> int:
    """
    Normalizes raw_score (0.0 to 10.0) to a 0–100 integer range.
    """
    normalized = round(raw_score * 10)
    return max(0, min(100, normalized))


def determine_risk_level(risk_score: int) -> str:
    """
    Maps an integer risk_score (0–100) to a deterministic risk level.
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
