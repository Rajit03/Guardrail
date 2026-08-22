import logging
from typing import List, Optional, Dict, Any, Tuple
import httpx

from app.scanners.base import FindingData, ScannerResult
from app.scanners.dependencies.scanner import BaseDependencyScanner
from app.scanners.dependencies.node import parse_node_dependencies
from app.scanners.dependencies.python import parse_python_dependencies

logger = logging.getLogger(__name__)

OSV_URL = "https://api.osv.dev/v1/querybatch"


def parse_cvss_vector_severity(vector: str) -> Optional[str]:
    """
    Basic CVSS v3 vector rating parser if numerical score is not directly supplied.
    """
    if not vector or not isinstance(vector, str):
        return None
    # If a direct float string like "8.5" was provided
    try:
        score = float(vector)
        if score >= 9.0: return "CRITICAL"
        if score >= 7.0: return "HIGH"
        if score >= 4.0: return "MEDIUM"
        if score > 0.0: return "LOW"
    except ValueError:
        pass

    # Simple heuristic on CVSS vector strings if CVSS:3.1/AV:N/AC:L...
    v_upper = vector.upper()
    if "AV:N" in v_upper and ("AC:L" in v_upper or "C:H" in v_upper or "I:H" in v_upper):
        if "PR:N" in v_upper:
            return "CRITICAL"
        return "HIGH"
    return None


def determine_osv_severity(vuln_data: dict) -> str:
    """
    Extracts or maps severity from OSV vulnerability record.
    Checks severity array (CVSS_V3), database_specific severity, and ecosystem_specific severity.
    Returns standard Guardrail severity: CRITICAL, HIGH, MEDIUM, LOW, INFO.
    """
    # 1. Check database_specific / ecosystem_specific severity strings
    for container_key in ("database_specific", "ecosystem_specific"):
        container = vuln_data.get(container_key)
        if isinstance(container, dict):
            sev_raw = container.get("severity") or container.get("cvss_severity")
            if isinstance(sev_raw, str):
                s_upper = sev_raw.upper()
                if s_upper == "MODERATE":
                    return "MEDIUM"
                if s_upper in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
                    return s_upper

    # 2. Check severity array in OSV record
    severities = vuln_data.get("severity", [])
    if isinstance(severities, list):
        for s in severities:
            if isinstance(s, dict):
                s_type = s.get("type")
                score_val = s.get("score")
                if s_type in ("CVSS_V3", "CVSS_V4") and score_val:
                    parsed = parse_cvss_vector_severity(str(score_val))
                    if parsed:
                        return parsed

    # Default to HIGH for confirmed OSV advisories if unspecified
    return "HIGH"


class OSVScanner(BaseDependencyScanner):
    """
    Dependency vulnerability scanner integrating with OSV.dev batch API.
    Performs static dependency inspection without executing repository code.
    """

    def scan(self, repository_path: str) -> ScannerResult:
        findings: List[FindingData] = []
        queries: List[Dict[str, Any]] = []
        file_map: List[Tuple[str, str, str]] = []

        # 1. Parse Node dependencies
        node_queries, node_map = parse_node_dependencies(repository_path)
        queries.extend(node_queries)
        file_map.extend(node_map)

        # 2. Parse Python dependencies
        python_queries, python_map = parse_python_dependencies(repository_path)
        queries.extend(python_queries)
        file_map.extend(python_map)

        if not queries:
            logger.info(f"No supported dependency manifest found in {repository_path}")
            return ScannerResult(
                scanner_name="osv",
                executed=True,
                status="SKIPPED",
                error_message="No supported dependency manifest files (e.g. requirements.txt, pyproject.toml, package.json) found in repository.",
                raw_findings_count=0,
                normalized_findings_count=0,
                findings=[]
            )

        # 3. Query OSV API in batch
        try:
            response = httpx.post(
                OSV_URL,
                json={"queries": queries},
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )

            if response.status_code != 200:
                err_msg = f"OSV API request failed with status code {response.status_code}: {response.text[:255]}"
                logger.error(err_msg)
                return ScannerResult(
                    scanner_name="osv",
                    executed=True,
                    status="FAILED",
                    error_message=err_msg,
                    findings=[]
                )

            data = response.json()
            results = data.get("results", [])
            raw_vulnerabilities_count = 0

            for i, res in enumerate(results):
                if i >= len(file_map):
                    break
                file_path, pkg_name, ver = file_map[i]
                vulns = res.get("vulns", [])

                if isinstance(vulns, list):
                    raw_vulnerabilities_count += len(vulns)
                    for vuln in vulns:
                        if not isinstance(vuln, dict):
                            continue

                        osv_id = vuln.get("id", "UNKNOWN-VULN")
                        aliases_list = vuln.get("aliases", [])
                        if not isinstance(aliases_list, list):
                            aliases_list = []

                        # Select primary vulnerability ID (prefer CVE if in aliases)
                        cve_alias = next((a for a in aliases_list if a.startswith("CVE-")), None)
                        primary_id = cve_alias if cve_alias else osv_id

                        summary = vuln.get("summary") or vuln.get("details") or f"Vulnerability detected in package '{pkg_name}'."
                        if len(summary) > 255:
                            summary = summary[:252] + "..."

                        severity = determine_osv_severity(vuln)

                        # Extract fixed version if available
                        fixed_version = None
                        if "affected" in vuln and isinstance(vuln["affected"], list):
                            for aff in vuln["affected"]:
                                ranges = aff.get("ranges", [])
                                if isinstance(ranges, list):
                                    for r in ranges:
                                        events = r.get("events", [])
                                        if isinstance(events, list):
                                            for ev in events:
                                                if isinstance(ev, dict) and "fixed" in ev:
                                                    fixed_version = str(ev["fixed"])
                                                    break

                        if fixed_version:
                            recommendation = f"Upgrade '{pkg_name}' from version {ver} to version {fixed_version} or higher."
                        else:
                            recommendation = f"Upgrade '{pkg_name}' from version {ver} to a patched release."

                        title = f"{pkg_name} vulnerability — {primary_id}"

                        finding = FindingData(
                            type="DEPENDENCY",
                            severity=severity,
                            title=title,
                            scanner="osv",
                            description=summary,
                            file_path=file_path,
                            line_number=None,
                            rule_id=primary_id,
                            evidence=f"Package '{pkg_name}' (version {ver}) in '{file_path}' is affected by {primary_id}.",
                            recommendation=recommendation,
                            package_name=pkg_name,
                            installed_version=ver,
                            fixed_version=fixed_version,
                            vulnerability_id=primary_id,
                            aliases=aliases_list
                        )
                        findings.append(finding)

            return ScannerResult(
                scanner_name="osv",
                executed=True,
                status="COMPLETED",
                error_message=None,
                raw_findings_count=raw_vulnerabilities_count,
                normalized_findings_count=len(findings),
                deduplicated_findings_count=len(findings),
                findings=findings
            )

        except Exception as e:
            err_msg = f"Error communicating with OSV API: {e}"
            logger.error(err_msg)
            return ScannerResult(
                scanner_name="osv",
                executed=True,
                status="FAILED",
                error_message=err_msg[:1024],
                findings=[]
            )
