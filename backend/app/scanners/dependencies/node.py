import json
import logging
import os
import re
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)


def parse_node_dependencies(repository_path: str) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str, str]]]:
    """
    Statically parses package.json and package-lock.json to extract npm dependencies.
    Never executes npm install or code from the repository.
    Returns:
        queries: List of dict objects formatted for OSV batch query
        file_map: List of tuples (file_path, package_name, version)
    """
    queries: List[Dict[str, Any]] = []
    file_map: List[Tuple[str, str, str]] = []
    seen = set()

    # 1. Parse package.json
    package_json_path = os.path.join(repository_path, "package.json")
    if os.path.exists(package_json_path):
        try:
            with open(package_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    deps = {}
                    if isinstance(data.get("dependencies"), dict):
                        deps.update(data["dependencies"])
                    if isinstance(data.get("devDependencies"), dict):
                        deps.update(data["devDependencies"])

                    for pkg, ver in deps.items():
                        if isinstance(pkg, str) and isinstance(ver, str):
                            # Remove non-numeric leading characters (e.g. ^1.2.3 -> 1.2.3)
                            clean_ver = re.sub(r'^[~^><=v]+', '', ver.strip())
                            key = ("npm", pkg, clean_ver)
                            if clean_ver and key not in seen:
                                seen.add(key)
                                queries.append({
                                    "package": {"name": pkg, "ecosystem": "npm"},
                                    "version": clean_ver
                                })
                                file_map.append(("package.json", pkg, clean_ver))
        except Exception as e:
            logger.error(f"Failed to parse package.json: {e}")

    # 2. Parse package-lock.json if present for precise lockfile versions
    package_lock_path = os.path.join(repository_path, "package-lock.json")
    if os.path.exists(package_lock_path):
        try:
            with open(package_lock_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # v2 / v3 lockfile format ("packages" dictionary)
                    packages = data.get("packages")
                    if isinstance(packages, dict):
                        for pkg_path, pkg_data in packages.items():
                            if isinstance(pkg_data, dict) and "version" in pkg_data:
                                ver = str(pkg_data["version"]).strip()
                                # Handle top-level or nested node_modules path
                                pkg_name = pkg_path.split("node_modules/")[-1] if "node_modules/" in pkg_path else pkg_path
                                if pkg_name and pkg_name != "" and not pkg_name.startswith("."):
                                    key = ("npm", pkg_name, ver)
                                    if ver and key not in seen:
                                        seen.add(key)
                                        queries.append({
                                            "package": {"name": pkg_name, "ecosystem": "npm"},
                                            "version": ver
                                        })
                                        file_map.append(("package-lock.json", pkg_name, ver))
                    # v1 lockfile format fallback ("dependencies" dictionary)
                    elif isinstance(data.get("dependencies"), dict):
                        for pkg_name, pkg_info in data["dependencies"].items():
                            if isinstance(pkg_info, dict) and "version" in pkg_info:
                                ver = str(pkg_info["version"]).strip()
                                key = ("npm", pkg_name, ver)
                                if ver and key not in seen:
                                    seen.add(key)
                                    queries.append({
                                        "package": {"name": pkg_name, "ecosystem": "npm"},
                                        "version": ver
                                    })
                                    file_map.append(("package-lock.json", pkg_name, ver))
        except Exception as e:
            logger.error(f"Failed to parse package-lock.json: {e}")

    return queries, file_map
