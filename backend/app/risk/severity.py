from typing import Dict

# Centralized severity base score mapping (on 0–100 scale)
SEVERITY_SCORES: Dict[str, float] = {
    "CRITICAL": 85.0,
    "HIGH": 65.0,
    "MEDIUM": 45.0,
    "LOW": 20.0,
    "INFO": 0.0
}


def get_severity_score(severity: str) -> float:
    """
    Returns deterministic numerical base score for a given severity label.
    Defaults to 45.0 (MEDIUM) if unknown.
    """
    if not severity:
        return 45.0
    sev_upper = severity.upper().strip()
    return SEVERITY_SCORES.get(sev_upper, 45.0)
