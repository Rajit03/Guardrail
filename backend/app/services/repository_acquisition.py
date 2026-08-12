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
    Context manager that safely downloads a GitHub repository as a zip archive,
    extracts it to a temporary directory, and yields the directory path.
    Cleans up the temporary directory when done.
    Does NOT execute any code from the repository.
    """
    # 1. Validate GitHub URL
    if not repository.url.startswith("https://github.com/"):
        raise ValueError("Only public GitHub repositories are supported.")

    # Parse owner and repo from URL (e.g., https://github.com/owner/repo)
    parts = repository.url.rstrip("/").split("/")
    if len(parts) < 5:
        raise ValueError("Invalid GitHub URL format.")
    
    owner = parts[-2]
    repo_name = parts[-1]
    
    # 2. Construct zip download URL
    branch = repository.default_branch or "main"
    zip_url = f"https://github.com/{owner}/{repo_name}/archive/refs/heads/{branch}.zip"

    # 3. Create temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, "repo.zip")
        extract_path = os.path.join(temp_dir, "extracted")
        os.makedirs(extract_path, exist_ok=True)
        
        # 4. Download zip
        try:
            with httpx.stream("GET", zip_url, follow_redirects=True, timeout=30.0) as r:
                r.raise_for_status()
                with open(zip_path, "wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
        except httpx.HTTPError as e:
            logger.error(f"Failed to download repository: {e}")
            raise Exception(f"Failed to download repository: HTTP Error. Verify it is public and branch '{branch}' exists.")

        # 5. Extract zip safely
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
        except zipfile.BadZipFile as e:
            logger.error(f"Bad zip file from GitHub: {e}")
            raise Exception("Failed to extract repository. Bad zip file.")

        # GitHub zip archives wrap everything in a single root folder (repo-branch)
        # We find that folder to yield
        extracted_items = os.listdir(extract_path)
        if len(extracted_items) == 1 and os.path.isdir(os.path.join(extract_path, extracted_items[0])):
            final_path = os.path.join(extract_path, extracted_items[0])
        else:
            final_path = extract_path

        yield final_path
