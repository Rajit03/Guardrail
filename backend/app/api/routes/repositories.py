import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.repository import RepositoryCreate, RepositoryUpdate, RepositoryResponse
from app.services.repository_service import RepositoryService
from app.api.dependencies import get_current_user
from app.models.user import User


router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def create_repository(
    repo_in: RepositoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RepositoryService(db)
    return service.create_repository(user_id=current_user.id, obj_in=repo_in)


from typing import List

@router.get("", response_model=dict[str, List[RepositoryResponse]])
def get_repositories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RepositoryService(db)
    repos = service.get_repositories(user_id=current_user.id)
    return {"repositories": repos}


@router.get("/{repository_id}", response_model=RepositoryResponse)
def get_repository(
    repository_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RepositoryService(db)
    repo = service.get_repository(user_id=current_user.id, repository_id=repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.patch("/{repository_id}", response_model=RepositoryResponse)
def update_repository(
    repository_id: uuid.UUID,
    repo_in: RepositoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RepositoryService(db)
    repo = service.update_repository(user_id=current_user.id, repository_id=repository_id, obj_in=repo_in)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.delete("/{repository_id}", response_model=dict)
def delete_repository(
    repository_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = RepositoryService(db)
    success = service.delete_repository(user_id=current_user.id, repository_id=repository_id)
    if not success:
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"message": "Repository deleted successfully"}
