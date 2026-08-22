import os
import zipfile
import tempfile
import httpx
import logging
from typing import Generator
from contextlib import contextmanager
from app.models.repository import Repository

logger = logging.getLogger(__name__)


@contextmanager
def acquire_repository(repository: Repository) -> Generator[str, None, None]:
    """
    Context manager that safely downloads a public GitHub repository as a zip archive,
    extracts it to a temporary directory, and yields the directory path.
    Cleans up the temporary directory when done.
    Does NOT execute any code from the repository.
    """
    # 1. Validate GitHub URL
    url = repository.url.strip()
    if not (url.startswith("https://github.com/") or url.startswith("http://github.com/")):
        raise ValueError("Only public GitHub repositories are currently supported by Guardrail.")

    # Disallow dangerous non-http protocols or internal targets
    parts = url.rstrip("/").split("/")
    if len(parts) < 5:
        raise ValueError("Invalid GitHub repository URL format.")

    owner = parts[-2]
    repo_name = parts[-1]
    if repo_name.endswith(".git"):
        repo_name = repo_name[:-4]

    # 2. Construct zip download URL
    branch = repository.default_branch or "main"
    zip_url = f"https://github.com/{owner}/{repo_name}/archive/refs/heads/{branch}.zip"

    # 3. Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "repo.zip")
        extract_path = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_path, exist_ok=True)

        # 4. Download zip safely
        try:
            with httpx.stream("GET", zip_url, follow_redirects=True, timeout=30.0) as r:
                if r.status_code in (401, 403, 404):
                    raise Exception(
                        "Scan failed. Guardrail could not obtain the repository contents. "
                        "Please verify that the repository is publicly accessible. "
                        "Private repository access will be available in a future Guardrail version."
                    )
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 403, 404):
                raise Exception(
                    "Scan failed. Guardrail could not obtain the repository contents. "
                    "Please verify that the repository is publicly accessible. "
                    "Private repository access will be available in a future Guardrail version."
                )
            raise Exception(f"Failed to download repository contents from GitHub (HTTP status {e.response.status_code}).")
        except httpx.HTTPError as e:
            logger.error(f"Failed to download repository: {e}")
            raise Exception(
                "Scan failed. Guardrail could not obtain the repository contents. "
                "Please verify that the repository is publicly accessible."
            )

        # 5. Extract zip safely
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Prevent path traversal vulnerabilities (Zip Slip)
                for member in zip_ref.infolist():
                    member_path = os.path.abspath(os.path.join(extract_path, member.filename))
                    if not member_path.startswith(os.path.abspath(extract_path)):
                        raise Exception("Security error: Zip archive contains invalid path traversal members.")
                zip_ref.extractall(extract_path)
        except zipfile.BadZipFile as e:
            logger.error(f"Bad zip file from GitHub: {e}")
            raise Exception("Failed to extract repository contents. Invalid or corrupt archive.")

        # GitHub zip archives wrap everything in a single root folder (repo-branch)
        extracted_items = os.listdir(extract_path)
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_path, extracted_items[0])):
            final_path = os.path.join(extract_path, extracted_items[0])
        else:
            final_path = extract_path

        yield final_path
