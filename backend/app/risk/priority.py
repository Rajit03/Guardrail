def determine_priority(
    severity: str,
    exposure: str,
    asset_criticality: str,
    risk_score: int
) -> str:
    """
    Determines action priority level deterministically based on multi-factor analysis:
    - P0: Immediate action required
    - P1: Urgent action required
    - P2: Important action required
    - P3: Routine action required
    """
    sev_upper = (severity or "MEDIUM").upper().strip()
    exp_upper = (exposure or "UNKNOWN").upper().strip()
    crit_upper = (asset_criticality or "UNKNOWN").upper().strip()
    score = max(0, min(100, risk_score))

    # P0 Conditions: Immediate action
    if sev_upper == "CRITICAL" and exp_upper in ("INTERNET", "EXTERNAL"):
        return "P0"
    if score >= 80 and exp_upper in ("INTERNET", "EXTERNAL"):
        return "P0"
    if score >= 85 and crit_upper in ("CRITICAL", "HIGH"):
        return "P0"

    # P1 Conditions: Urgent action
    if sev_upper == "CRITICAL":
        return "P1"
    if score >= 80:
        return "P1"
    if sev_upper == "HIGH" and exp_upper in ("INTERNET", "EXTERNAL"):
        return "P1"
    if score >= 60:
        return "P1"

    # P2 Conditions: Important action
    if sev_upper == "HIGH":
        return "P2"
    if sev_upper == "MEDIUM" and exp_upper in ("INTERNET", "EXTERNAL", "INTERNAL"):
        return "P2"
    if score >= 35:
        return "P2"

    # P3 Conditions: Routine maintenance
    return "P3"
