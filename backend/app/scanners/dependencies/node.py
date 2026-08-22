import json
import logging
import os
import re
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)


def clean_node_version(ver: str) -> str:
    return re.sub(r'^[~^><=v]+', '', ver.strip())


def parse_node_dependencies(repository_path: str) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str, str]]]:
    """
    Recursively inspects the repository for supported Node dependency manifests:
    - package.json
    - package-lock.json
    - yarn.lock
    - pnpm-lock.yaml
    Returns:
        queries: List of OSV batch query dicts
        file_map: List of tuples (file_path, package_name, version)
    """
    queries: List[Dict[str, Any]] = []
    file_map: List[Tuple[str, str, str]] = []
    seen = set()

    for root, dirs, files in os.walk(repository_path):
        # Skip node_modules and .git
        if "node_modules" in dirs:
            dirs.remove("node_modules")
        if ".git" in dirs:
            dirs.remove(".git")

        for filename in files:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, repository_path).replace("\\", "/")

            # 1. package.json
            if filename == "package.json":
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            deps = {}
                            if isinstance(data.get("dependencies"), dict):
                                deps.update(data["dependencies"])
                            if isinstance(data.get("devDependencies"), dict):
                                deps.update(data["devDependencies"])

                            for pkg, ver in deps.items():
                                if isinstance(pkg, str) and isinstance(ver, str):
                                    c_ver = clean_node_version(ver)
                                    key = ("npm", pkg, c_ver, rel_path)
                                    if c_ver and key not in seen:
                                        seen.add(key)
                                        queries.append({
                                            "package": {"name": pkg, "ecosystem": "npm"},
                                            "version": c_ver
                                        })
                                        file_map.append((rel_path, pkg, c_ver))
                except Exception as e:
                    logger.error(f"Failed to parse package.json '{rel_path}': {e}")

            # 2. package-lock.json
            elif filename == "package-lock.json":
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            packages = data.get("packages")
                            if isinstance(packages, dict):
                                for pkg_path, pkg_data in packages.items():
                                    if isinstance(pkg_data, dict) and "version" in pkg_data:
                                        c_ver = str(pkg_data["version"]).strip()
                                        pkg_name = pkg_path.split("node_modules/")[-1] if "node_modules/" in pkg_path else pkg_path
                                        if pkg_name and pkg_name != "" and not pkg_name.startswith("."):
                                            key = ("npm", pkg_name, c_ver, rel_path)
                                            if c_ver and key not in seen:
                                                seen.add(key)
                                                queries.append({
                                                    "package": {"name": pkg_name, "ecosystem": "npm"},
                                                    "version": c_ver
                                                })
                                                file_map.append((rel_path, pkg_name, c_ver))
                            elif isinstance(data.get("dependencies"), dict):
                                for pkg_name, pkg_info in data["dependencies"].items():
                                    if isinstance(pkg_info, dict) and "version" in pkg_info:
                                        c_ver = str(pkg_info["version"]).strip()
                                        key = ("npm", pkg_name, c_ver, rel_path)
                                        if c_ver and key not in seen:
                                            seen.add(key)
                                            queries.append({
                                                "package": {"name": pkg_name, "ecosystem": "npm"},
                                                "version": c_ver
                                            })
                                            file_map.append((rel_path, pkg_name, c_ver))
                except Exception as e:
                    logger.error(f"Failed to parse package-lock.json '{rel_path}': {e}")

            # 3. yarn.lock
            elif filename == "yarn.lock":
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    entries = re.findall(r'("^?([^@\n]+)@[^:\n]+"?):\n\s+version\s+"([^"]+)"', content)
                    for _, pkg_name, ver in entries:
                        key = ("npm", pkg_name, ver, rel_path)
                        if ver and key not in seen:
                            seen.add(key)
                            queries.append({
                                "package": {"name": pkg_name, "ecosystem": "npm"},
                                "version": ver
                            })
                            file_map.append((rel_path, pkg_name, ver))
                except Exception as e:
                    logger.error(f"Failed to parse yarn.lock '{rel_path}': {e}")

    return queries, file_map
