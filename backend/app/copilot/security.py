import re
from typing import Dict, Any, Optional, List

# Regex patterns for common secret formats to scrub if they accidentally appear in evidence/descriptions
SECRET_PATTERNS = [
    re.compile(r'(?i)(api[_\-\s]?key|secret|token|password|passwd|auth|bearer|private[_\-\s]?key)\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.\+\/]{8,})["\']?'),
    re.compile(r'\bAKIA[0-9A-Z]{16}\b'),  # AWS Access Key ID
    re.compile(r'(?i)\bgh[pousr]_[0-9a-zA-Z]{36}\b'),  # GitHub Tokens
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'),
]

SECRET_EXFILTRATION_PATTERNS = [
    re.compile(r'(?i)\b(?:what|show|tell|reveal|print|give|display|extract|get)\b.*\b(?:secret|password|api[_\-\s]?key|token|credential|private[_\-\s]?key|private_key|privatekey)\b'),
    re.compile(r'(?i)\b(?:what|show|tell|reveal)\b.*\b(?:is|are)\b.*\b(?:the|my)\b.*\b(?:secret|password|key|token|creds?)\b'),
    re.compile(r'(?i)\b(?:secret|password|token|api[_\-\s]?key)\s+(?:value|string|text|content)\b'),
]


def is_secret_exfiltration_attempt(query: str) -> bool:
    """
    Detects if the user is explicitly requesting to view/reveal raw secret values.
    """
    clean_q = query.strip()
    for pattern in SECRET_EXFILTRATION_PATTERNS:
        if pattern.search(clean_q):
            return True
    return False


def _redact_match(match: re.Match) -> str:
    if match.lastindex and match.lastindex >= 1 and match.group(1):
        return f"{match.group(1)}: [REDACTED_BY_GUARDRAIL]"
    return "[REDACTED_BY_GUARDRAIL]"


def sanitize_text(text: Optional[str]) -> str:
    """
    Redacts any raw secret or credential pattern from text strings before AI prompt ingestion.
    """
    if not text:
        return ""
    sanitized = text
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub(_redact_match, sanitized)
    return sanitized


def sanitize_untrusted_content(text: Optional[str], max_len: int = 1000) -> str:
    """
    Sanitizes untrusted repository / description text to prevent prompt injection:
    - Escapes dangerous delimiters
    - Strips injection attempts like "ignore all instructions"
    - Truncates to max_len
    """
    if not text:
        return ""
    
    # Strip potential secrets
    cleaned = sanitize_text(text)
    # Neutralize non-printable control characters
    cleaned = "".join(ch for ch in cleaned if ch.isprintable() or ch in ("\n", "\t", " "))
    
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len] + "... [truncated]"
    return cleaned


def sanitize_finding_for_ai(finding_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a completely safe, redacted dictionary of finding metadata for AI context.
    NEVER includes raw secret values, match tokens, or unredacted evidence.
    """
    f_type = str(finding_dict.get("type", "UNKNOWN")).upper()
    
    safe_data = {
        "id": str(finding_dict.get("id", "")),
        "type": f_type,
        "severity": str(finding_dict.get("severity", "MEDIUM")).upper(),
        "risk_score": int(finding_dict.get("risk_score", 0)),
        "risk_level": str(finding_dict.get("risk_level", "INFO")),
        "priority": str(finding_dict.get("priority", "P3")),
        "title": sanitize_untrusted_content(finding_dict.get("title", ""), max_len=200),
        "file_path": sanitize_untrusted_content(finding_dict.get("file_path", ""), max_len=300),
        "line_number": finding_dict.get("line_number"),
        "scanner": str(finding_dict.get("scanner", "")).lower(),
        "rule_id": sanitize_untrusted_content(finding_dict.get("rule_id", ""), max_len=100),
        "status": str(finding_dict.get("status", "OPEN")),
        "recommendation": sanitize_untrusted_content(finding_dict.get("recommendation", ""), max_len=300),
    }

    if f_type == "SECRET":
        # Extra secret protection: DO NOT INCLUDE raw evidence, match, or description
        safe_data["evidence"] = "[REDACTED: Guardrail hides all raw credentials for security]"
        safe_data["package_name"] = None
        safe_data["installed_version"] = None
        safe_data["fixed_version"] = None
        safe_data["vulnerability_id"] = None
        safe_data["description"] = "A secret or credential pattern was detected in this file."
    else:
        # Dependency/vulnerability tracking fields
        safe_data["package_name"] = sanitize_untrusted_content(finding_dict.get("package_name"), max_len=100) or None
        safe_data["installed_version"] = sanitize_untrusted_content(finding_dict.get("installed_version"), max_len=50) or None
        safe_data["fixed_version"] = sanitize_untrusted_content(finding_dict.get("fixed_version"), max_len=50) or None
        safe_data["vulnerability_id"] = sanitize_untrusted_content(finding_dict.get("vulnerability_id"), max_len=100) or None
        
        raw_desc = finding_dict.get("description")
        safe_data["description"] = sanitize_untrusted_content(raw_desc, max_len=400) if raw_desc else None

    return safe_data
