import logging
import os
import re
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)


def clean_version(raw_ver: str) -> str:
    """Removes specifiers like ==, >=, ^, ~, = to get a clean version string."""
    clean = re.sub(r'^[~^><=v]+', '', raw_ver.strip())
    # Handle version qualifiers like 2.19.1;python_version>'3.6'
    clean = clean.split(';')[0].strip()
    return clean


def parse_python_dependencies(repository_path: str) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str, str]]]:
    """
    Recursively inspects the repository for supported Python dependency manifests:
    - requirements.txt (and requirements/*.txt)
    - pyproject.toml
    - poetry.lock
    - Pipfile
    - Pipfile.lock
    Returns:
        queries: List of OSV batch query dicts
        file_map: List of tuples (file_path, package_name, version)
    """
    queries: List[Dict[str, Any]] = []
    file_map: List[Tuple[str, str, str]] = []
    seen = set()

    for root, dirs, files in os.walk(repository_path):
        # Skip .git directory
        if ".git" in dirs:
            dirs.remove(".git")

        for filename in files:
            full_path = os.path.join(root, filename)
            rel_path = os.path.relpath(full_path, repository_path).replace("\\", "/")

            # 1. requirements.txt or *.txt inside requirements/
            if filename == "requirements.txt" or (filename.endswith(".txt") and "requirements" in root.lower()):
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            line = line.strip()
                            if not line or line.startswith("#") or line.startswith("-"):
                                continue
                            match = re.match(r'^([a-zA-Z0-9_\-\.]+)\s*(?:==|>=|~=)\s*([a-zA-Z0-9_\-\.]+)', line)
                            if match:
                                pkg, ver = match.groups()
                                ver = clean_version(ver)
                                key = ("PyPI", pkg.lower(), ver, rel_path)
                                if ver and key not in seen:
                                    seen.add(key)
                                    queries.append({
                                        "package": {"name": pkg, "ecosystem": "PyPI"},
                                        "version": ver
                                    })
                                    file_map.append((rel_path, pkg, ver))
                except Exception as e:
                    logger.error(f"Failed to parse requirements file '{rel_path}': {e}")

            # 2. pyproject.toml
            elif filename == "pyproject.toml":
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    # Find dependencies under [project.dependencies]
                    proj_deps = re.findall(r'"([a-zA-Z0-9_\-\.]+)\s*(?:==|>=|~=|^)\s*([a-zA-Z0-9_\-\.]+)"', content)
                    for pkg, ver in proj_deps:
                        ver = clean_version(ver)
                        key = ("PyPI", pkg.lower(), ver, rel_path)
                        if ver and key not in seen:
                            seen.add(key)
                            queries.append({
                                "package": {"name": pkg, "ecosystem": "PyPI"},
                                "version": ver
                            })
                            file_map.append((rel_path, pkg, ver))

                    # Find dependencies under [tool.poetry.dependencies]
                    poetry_deps = re.findall(r'([a-zA-Z0-9_\-\.]+)\s*=\s*"[~^>=]*([a-zA-Z0-9_\-\.]+)"', content)
                    for pkg, ver in poetry_deps:
                        if pkg.lower() == "python":
                            continue
                        ver = clean_version(ver)
                        key = ("PyPI", pkg.lower(), ver, rel_path)
                        if ver and key not in seen:
                            seen.add(key)
                            queries.append({
                                "package": {"name": pkg, "ecosystem": "PyPI"},
                                "version": ver
                            })
                            file_map.append((rel_path, pkg, ver))
                except Exception as e:
                    logger.error(f"Failed to parse pyproject.toml '{rel_path}': {e}")

            # 3. poetry.lock
            elif filename == "poetry.lock":
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    blocks = content.split("[[package]]")
                    for b in blocks[1:]:
                        name_match = re.search(r'name\s*=\s*"([^"]+)"', b)
                        ver_match = re.search(r'version\s*=\s*"([^"]+)"', b)
                        if name_match and ver_match:
                            pkg = name_match.group(1)
                            ver = ver_match.group(1)
                            key = ("PyPI", pkg.lower(), ver, rel_path)
                            if ver and key not in seen:
                                seen.add(key)
                                queries.append({
                                    "package": {"name": pkg, "ecosystem": "PyPI"},
                                    "version": ver
                                })
                                file_map.append((rel_path, pkg, ver))
                except Exception as e:
                    logger.error(f"Failed to parse poetry.lock '{rel_path}': {e}")

            # 4. Pipfile
            elif filename == "Pipfile":
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    matches = re.findall(r'([a-zA-Z0-9_\-\.]+)\s*=\s*"[==>=~]*([a-zA-Z0-9_\-\.]+)"', content)
                    for pkg, ver in matches:
                        ver = clean_version(ver)
                        key = ("PyPI", pkg.lower(), ver, rel_path)
                        if ver and key not in seen:
                            seen.add(key)
                            queries.append({
                                "package": {"name": pkg, "ecosystem": "PyPI"},
                                "version": ver
                            })
                            file_map.append((rel_path, pkg, ver))
                except Exception as e:
                    logger.error(f"Failed to parse Pipfile '{rel_path}': {e}")

    return queries, file_map
