import json
import logging
import os
import re
from typing import List, Dict, Any

import httpx
from ..base import BaseScanner, FindingData

logger = logging.getLogger(__name__)

OSV_URL = "https://api.osv.dev/v1/querybatch"

class OSVScanner(BaseScanner):
    def scan(self, repository_path: str) -> List[FindingData]:
        findings = []
        queries = []
        file_map = []  # To map query index back to file and package

        # 1. Parse package.json
        package_json_path = os.path.join(repository_path, "package.json")
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    for pkg, ver in deps.items():
                        # Basic cleanup of version strings (e.g., ^1.2.3 -> 1.2.3)
                        clean_ver = re.sub(r'^[~^><=]+', '', ver)
                        queries.append({
                            "package": {"name": pkg, "ecosystem": "npm"},
                            "version": clean_ver
                        })
                        file_map.append(("package.json", pkg, clean_ver))
            except Exception as e:
                logger.error(f"Failed to parse package.json: {e}")

        # 2. Parse package-lock.json (very simplified, usually better to parse lockfile properly)
        # For simplicity, we just use package.json in this MVP if lock is too complex, but let's try a basic lockfile parse
        package_lock_path = os.path.join(repository_path, "package-lock.json")
        if os.path.exists(package_lock_path):
            try:
                with open(package_lock_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "packages" in data:
                        for pkg_path, pkg_data in data["packages"].items():
                            if pkg_path and "version" in pkg_data:
                                pkg_name = pkg_path.split("node_modules/")[-1]
                                ver = pkg_data["version"]
                                queries.append({
                                    "package": {"name": pkg_name, "ecosystem": "npm"},
                                    "version": ver
                                })
                                file_map.append(("package-lock.json", pkg_name, ver))
            except Exception as e:
                logger.error(f"Failed to parse package-lock.json: {e}")

        # 3. Parse requirements.txt
        req_path = os.path.join(repository_path, "requirements.txt")
        if os.path.exists(req_path):
            try:
                with open(req_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Match package==version
                            match = re.match(r'^([a-zA-Z0-9_\-]+)==([a-zA-Z0-9_\.\-]+)', line)
                            if match:
                                pkg, ver = match.groups()
                                queries.append({
                                    "package": {"name": pkg, "ecosystem": "PyPI"},
                                    "version": ver
                                })
                                file_map.append(("requirements.txt", pkg, ver))
            except Exception as e:
                logger.error(f"Failed to parse requirements.txt: {e}")

        if not queries:
            return findings

        # Query OSV
        try:
            # Chunking requests if they are too large, but for MVP send all at once
            response = httpx.post(OSV_URL, json={"queries": queries}, timeout=30.0)
            if response.status_code == 200:
                results = response.json().get("results", [])
                for i, res in enumerate(results):
                    vulns = res.get("vulns", [])
                    if vulns:
                        file_path, pkg_name, ver = file_map[i]
                        for vuln in vulns:
                            finding = FindingData(
                                type="DEPENDENCY",
                                severity="HIGH", # Could map from OSV severity if present
                                title=f"Vulnerable dependency detected: {pkg_name}",
                                scanner="osv",
                                description=vuln.get("summary", "Installed package version is affected by a known vulnerability."),
                                file_path=file_path,
                                rule_id=vuln.get("id", ""),
                                evidence=f"Package {pkg_name}@{ver} has vulnerability {vuln.get('id')}",
                                recommendation="Upgrade to a fixed version or review the vulnerability details."
                            )
                            findings.append(finding)
        except Exception as e:
            logger.error(f"Error querying OSV API: {e}")

        return findings
