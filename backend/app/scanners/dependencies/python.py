import logging
import os
import re
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)


def parse_python_dependencies(repository_path: str) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str, str]]]:
    """
    Statically parses requirements.txt to extract PyPI dependencies.
    Never executes python setup.py or pip install.
    Returns:
        queries: List of dict objects formatted for OSV batch query
        file_map: List of tuples (file_path, package_name, version)
    """
    queries: List[Dict[str, Any]] = []
    file_map: List[Tuple[str, str, str]] = []
    seen = set()

    req_path = os.path.join(repository_path, "requirements.txt")
    if os.path.exists(req_path):
        try:
            with open(req_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines, comments, and flags like -r or -e
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue
                    
                    # Match package==version or package>=version etc.
                    match = re.match(r'^([a-zA-Z0-9_\-\.]+)\s*==\s*([a-zA-Z0-9_\-\.]+)', line)
                    if match:
                        pkg, ver = match.groups()
                        key = ("PyPI", pkg, ver)
                        if key not in seen:
                            seen.add(key)
                            queries.append({
                                "package": {"name": pkg, "ecosystem": "PyPI"},
                                "version": ver
                            })
                            file_map.append(("requirements.txt", pkg, ver))
        except Exception as e:
            logger.error(f"Failed to parse requirements.txt: {e}")

    return queries, file_map
