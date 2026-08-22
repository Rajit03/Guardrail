import logging
from typing import List
import httpx

from app.scanners.base import FindingData
from app.scanners.dependencies.scanner import BaseDependencyScanner
from app.scanners.dependencies.node import parse_node_dependencies
from app.scanners.dependencies.python import parse_python_dependencies

logger = logging.getLogger(__name__)

OSV_URL = "https://api.osv.dev/v1/querybatch"


def determine_severity(vuln_data: dict) -> str:
    """
    Extracts or maps severity from OSV vulnerability record.
    Returns standard Guardrail severity string: CRITICAL, HIGH, MEDIUM, LOW, INFO.
    """
    # Check severity field in OSV record
    severities = vuln_data.get("severity", [])
    if isinstance(severities, list):
        for s in severities:
            if isinstance(s, dict) and s.get("type") == "CVSS_V3":
                score_str = s.get("score", "")
                # Basic CVSS parsing if score string is a float like "8.5"
                try:
                    score = float(score_str)
                    if score >= 9.0:
                        return "CRITICAL"
                    elif score >= 7.0:
                        return "HIGH"
                    elif score >= 4.0:
                        return "MEDIUM"
                    elif score > 0.0:
                        return "LOW"
                except ValueError:
                    pass

    # Check database_specific severity if present
    db_specific = vuln_data.get("database_specific", {})
    if isinstance(db_specific, dict):
        sev_str = str(db_specific.get("severity", "")).upper()
        if sev_str in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
            return sev_str

    # Default to HIGH for known vulnerabilities
    return "HIGH"


class OSVScanner(BaseDependencyScanner):
    """
    Dependency vulnerability scanner integrating with OSV.dev.
    Statically inspects dependency manifests without executing repository code.
    """

    def scan(self, repository_path: str) -> List[FindingData]:
        findings: List[FindingData] = []
        queries = []
        file_map = []

        # 1. Parse Node dependencies
        node_queries, node_map = parse_node_dependencies(repository_path)
        queries.extend(node_queries)
        file_map.extend(node_map)

        # 2. Parse Python dependencies
        python_queries, python_map = parse_python_dependencies(repository_path)
        queries.extend(python_queries)
        file_map.extend(python_map)

        if not queries:
            return findings

        # 3. Query OSV API in batch
        try:
            # Send batch query to OSV API with 30s timeout
            response = httpx.post(
                OSV_URL,
                json={"queries": queries},
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                for i, res in enumerate(results):
                    if i >= len(file_map):
                        break
                    file_path, pkg_name, ver = file_map[i]
                    vulns = res.get("vulns", [])

                    if isinstance(vulns, list):
                        for vuln in vulns:
                            if not isinstance(vuln, dict):
                                continue
                            vuln_id = vuln.get("id", "UNKNOWN-VULN")
                            summary = vuln.get("summary") or vuln.get("details") or "Known dependency vulnerability detected."
                            if len(summary) > 255:
                                summary = summary[:252] + "..."

                            severity = determine_severity(vuln)

                            recommendation = f"Upgrade '{pkg_name}' from version {ver} to a fixed release."
                            if "affected" in vuln and isinstance(vuln["affected"], list):
                                for aff in vuln["affected"]:
                                    ranges = aff.get("ranges", [])
                                    for r in ranges:
                                        events = r.get("events", [])
                                        for ev in events:
                                            if "fixed" in ev:
                                                recommendation = f"Upgrade '{pkg_name}' to version {ev['fixed']} or higher."

                            finding = FindingData(
                                type="DEPENDENCY",
                                severity=severity,
                                title=f"Vulnerable dependency detected: {pkg_name}",
                                scanner="osv",
                                description=summary,
                                file_path=file_path,
                                line_number=None,
                                rule_id=vuln_id,
                                evidence=f"Package '{pkg_name}' (version {ver}) is affected by {vuln_id}.",
                                recommendation=recommendation
                            )
                            findings.append(finding)
            else:
                logger.error(f"OSV API returned status code {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Error querying OSV API: {e}")

        return findings
