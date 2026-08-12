import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.repository import Repository
from app.schemas.repository import RepositoryCreate, RepositoryUpdate


class RepositoryService:
    def __init__(self, db: Session):
        self.db = db

    def create_repository(self, user_id: uuid.UUID, obj_in: RepositoryCreate) -> Repository:
        db_obj = Repository(
            user_id=user_id,
            name=obj_in.name,
            url=obj_in.url,
            provider=obj_in.provider,
            default_branch=obj_in.default_branch,
            description=obj_in.description
        )
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get_repositories(self, user_id: uuid.UUID) -> List[Repository]:
        return self.db.scalars(
            select(Repository)
            .where(Repository.user_id == user_id)
            .order_by(Repository.created_at.desc())
        ).all()

    def get_repository(self, user_id: uuid.UUID, repository_id: uuid.UUID) -> Optional[Repository]:
        return self.db.scalar(
            select(Repository)
            .where(Repository.user_id == user_id, Repository.id == repository_id)
        )

    def update_repository(
        self, user_id: uuid.UUID, repository_id: uuid.UUID, obj_in: RepositoryUpdate
    ) -> Optional[Repository]:
        db_obj = self.get_repository(user_id=user_id, repository_id=repository_id)
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete_repository(self, user_id: uuid.UUID, repository_id: uuid.UUID) -> bool:
        db_obj = self.get_repository(user_id=user_id, repository_id=repository_id)
        if not db_obj:
            return False

        self.db.delete(db_obj)
        self.db.commit()
        return True
