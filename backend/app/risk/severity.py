from typing import Dict

# Centralized severity score mapping
SEVERITY_SCORES: Dict[str, float] = {
    "CRITICAL": 10.0,
    "HIGH": 8.0,
    "MEDIUM": 5.0,
    "LOW": 2.0,
    "INFO": 0.0
}


def get_severity_score(severity: str) -> float:
    """
    Returns deterministic numerical severity score for a given severity label.
    Defaults to 5.0 (MEDIUM) if unknown.
    """
    if not severity:
        return 5.0
    sev_upper = severity.upper().strip()
    return SEVERITY_SCORES.get(sev_upper, 5.0)
