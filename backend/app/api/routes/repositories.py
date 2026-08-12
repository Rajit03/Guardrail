import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.repository import (
    RepositoryCreate,
    RepositoryUpdate,
    RepositoryOut,
    RepositoryListOut,
)
from app.schemas.user import MessageResponse
from app.services import repository_service
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.repository import Repository

router = APIRouter(prefix="/repositories", tags=["Repositories"])


def _get_owned_repository_or_404(
    db: Session,
    current_user: User,
    repository_id: uuid.UUID
) -> Repository:
    """Fetch a repository owned by the current user or raise 404.

    Returns 404 (not 403) for repositories owned by other users so their
    existence is not revealed.
    """
    repository = repository_service.get_repository(
        db, user_id=current_user.id, repository_id=repository_id
    )
    if repository is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found"
        )
    return repository


@router.post(
    "",
    response_model=RepositoryOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new repository"
)
def create_repository(
    repo_in: RepositoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register a repository owned by the authenticated user."""
    return repository_service.create_repository(
        db, user_id=current_user.id, repo_in=repo_in
    )


@router.get(
    "",
    response_model=RepositoryListOut,
    summary="List repositories of the authenticated user"
)
def list_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all repositories owned by the authenticated user."""
    repositories = repository_service.list_repositories(db, user_id=current_user.id)
    return {"repositories": repositories}


@router.get(
    "/{repository_id}",
    response_model=RepositoryOut,
    summary="Get repository details"
)
def get_repository(
    repository_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Return details of a repository owned by the authenticated user."""
    return _get_owned_repository_or_404(db, current_user, repository_id)


@router.patch(
    "/{repository_id}",
    response_model=RepositoryOut,
    summary="Update repository"
)
def update_repository(
    repository_id: uuid.UUID,
    repo_in: RepositoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Partially update a repository owned by the authenticated user.

    The repository URL, id, owner, and timestamps are immutable.
    """
    repository = _get_owned_repository_or_404(db, current_user, repository_id)
    return repository_service.update_repository(db, repository=repository, repo_in=repo_in)


@router.delete(
    "/{repository_id}",
    response_model=MessageResponse,
    summary="Delete repository"
)
def delete_repository(
    repository_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a repository owned by the authenticated user."""
    repository = _get_owned_repository_or_404(db, current_user, repository_id)
    repository_service.delete_repository(db, repository=repository)
    return {"message": "Repository deleted successfully"}
