import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.repository import Repository
from app.schemas.repository import RepositoryCreate, RepositoryUpdate


def create_repository(db: Session, user_id: uuid.UUID, repo_in: RepositoryCreate) -> Repository:
    """Create a new repository owned by the given user."""
    db_repo = Repository(
        user_id=user_id,
        name=repo_in.name,
        url=repo_in.url,
        provider=repo_in.provider.value,
        default_branch=repo_in.default_branch,
        description=repo_in.description,
        is_active=True
    )
    db.add(db_repo)
    db.commit()
    db.refresh(db_repo)
    return db_repo


def list_repositories(db: Session, user_id: uuid.UUID) -> List[Repository]:
    """List all repositories owned by the given user."""
    stmt = (
        select(Repository)
        .where(Repository.user_id == user_id)
        .order_by(Repository.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_repository(db: Session, user_id: uuid.UUID, repository_id: uuid.UUID) -> Optional[Repository]:
    """Retrieve a repository by id, scoped to the owning user."""
    stmt = select(Repository).where(
        Repository.id == repository_id,
        Repository.user_id == user_id
    )
    return db.scalars(stmt).first()


def update_repository(db: Session, repository: Repository, repo_in: RepositoryUpdate) -> Repository:
    """Apply partial updates to a repository."""
    update_data = repo_in.model_dump(exclude_unset=True)
    if "name" in update_data:
        repository.name = update_data["name"]
    if "default_branch" in update_data:
        repository.default_branch = update_data["default_branch"]
    if "description" in update_data:
        repository.description = update_data["description"]
    if "is_active" in update_data:
        repository.is_active = update_data["is_active"]
    db.commit()
    db.refresh(repository)
    return repository


def delete_repository(db: Session, repository: Repository) -> None:
    """Delete a repository."""
    db.delete(repository)
    db.commit()
