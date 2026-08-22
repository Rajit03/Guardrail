from typing import Optional


def generate_explanation(
    type_: str,
    severity: str,
    title: str,
    risk_level: str,
    priority: str,
    exposure: str = "UNKNOWN",
    asset_criticality: str = "UNKNOWN",
    file_path: Optional[str] = None,
) -> str:
    """
    Generates a clear, non-alarmist, deterministic explanation of the security risk.
    Does NOT use AI or claim active compromise.
    """
    finding_type = (type_ or "SECURITY").upper()
    sev = (severity or "MEDIUM").upper()
    location_str = f" in '{file_path}'" if file_path else ""

    parts = []

    if finding_type == "SECRET":
        parts.append(
            f"A potential hardcoded secret or credential ({title}) was identified{location_str} with {sev} severity."
        )
        parts.append(
            "Hardcoded credentials in source control create a risk of unauthorized access if source code is exposed or leaked."
        )
    elif finding_type == "DEPENDENCY":
        parts.append(
            f"A vulnerable package dependency ({title}) was detected{location_str} with {sev} severity."
        )
        parts.append(
            "Known vulnerabilities in third-party libraries could allow attackers to exploit software flaws or compromise application stability."
        )
    else:
        parts.append(
            f"A security issue ({title}) was detected{location_str} with {sev} severity."
        )

    # Contextual impact sentence
    if risk_level in ("CRITICAL", "HIGH"):
        parts.append(
            f"Given the {risk_level.lower()} risk level and {priority} priority, this issue presents a significant potential security impact and should be prioritized for review."
        )
    else:
        parts.append(
            f"This issue is classified as {risk_level.lower()} risk ({priority} priority) and should be addressed during routine maintenance."
        )

    return " ".join(parts)


def generate_remediation_guidance(type_: str, recommendation: Optional[str] = None) -> str:
    """
    Generates deterministic remediation guidance based on finding type.
    """
    finding_type = (type_ or "").upper()

    if finding_type == "SECRET":
        steps = [
            "1. Revoke or rotate the exposed credential immediately in the target service.",
            "2. Remove the credential from source control files.",
            "3. Audit repository git history to ensure historical commits do not retain the credential.",
            "4. Store sensitive credentials in secure environment variables or a dedicated secrets manager.",
            "5. Re-scan the repository to confirm resolution."
        ]
        if recommendation:
            steps.insert(0, f"Specific Scanner Note: {recommendation}\n")
        return "\n".join(steps)

    elif finding_type == "DEPENDENCY":
        steps = [
            "1. Identify the affected dependency manifest file (e.g. package.json or requirements.txt).",
            "2. Upgrade the affected package to a patched/fixed version.",
            "3. Run automated unit and integration tests to verify application compatibility.",
            "4. Re-scan the repository to verify the vulnerability has been resolved."
        ]
        if recommendation:
            steps.insert(0, f"Specific Patch Note: {recommendation}\n")
        return "\n".join(steps)

    else:
        steps = [
            "1. Inspect the affected file and line location.",
            "2. Apply recommended security fixes or code modifications.",
            "3. Re-scan the repository to confirm resolution."
        ]
        if recommendation:
            steps.insert(0, f"Recommendation: {recommendation}\n")
        return "\n".join(steps)
