import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.repository import Repository
from app.models.scan import Scan
from app.models.finding import Finding
from app.schemas.repository import RepositoryCreate, RepositoryUpdate


def _annotate_repository(db: Session, repo: Repository) -> Repository:
    """
    Annotate a Repository object with computed fields (findings_count,
    last_scan_status) using efficient SQL queries rather than ORM lazy loads.
    """
    findings_count = db.scalar(
        select(func.count()).select_from(Finding)
        .where(Finding.repository_id == repo.id, Finding.status == "OPEN")
    ) or 0
    repo.findings_count = findings_count

    latest_scan = db.scalar(
        select(Scan)
        .where(Scan.repository_id == repo.id)
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    repo.last_scan_status = latest_scan.status if latest_scan else None
    return repo


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
        db_obj.findings_count = 0
        db_obj.last_scan_status = None
        return db_obj

    def get_repositories(self, user_id: uuid.UUID) -> List[Repository]:
        repos = self.db.scalars(
            select(Repository)
            .where(Repository.user_id == user_id)
            .order_by(Repository.created_at.desc())
        ).all()
        for repo in repos:
            _annotate_repository(self.db, repo)
        return repos

    def get_repository(self, user_id: uuid.UUID, repository_id: uuid.UUID) -> Optional[Repository]:
        repo = self.db.scalar(
            select(Repository)
            .where(Repository.user_id == user_id, Repository.id == repository_id)
        )
        if repo:
            _annotate_repository(self.db, repo)
        return repo

    def get_repository_scans(self, user_id: uuid.UUID, repository_id: uuid.UUID) -> Optional[List[Scan]]:
        """Return scans for a repository, only if the user owns it."""
        repo = self.db.scalar(
            select(Repository)
            .where(Repository.user_id == user_id, Repository.id == repository_id)
        )
        if not repo:
            return None
        scans = self.db.scalars(
            select(Scan)
            .where(Scan.repository_id == repository_id)
            .order_by(Scan.created_at.desc())
        ).all()
        return list(scans)

    def update_repository(
        self, user_id: uuid.UUID, repository_id: uuid.UUID, obj_in: RepositoryUpdate
    ) -> Optional[Repository]:
        db_obj = self.db.scalar(
            select(Repository)
            .where(Repository.user_id == user_id, Repository.id == repository_id)
        )
        if not db_obj:
            return None

        update_data = obj_in.model_dump(exclude_unset=True)
        for field in update_data:
            setattr(db_obj, field, update_data[field])

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        _annotate_repository(self.db, db_obj)
        return db_obj

    def delete_repository(self, user_id: uuid.UUID, repository_id: uuid.UUID) -> bool:
        db_obj = self.db.scalar(
            select(Repository)
            .where(Repository.user_id == user_id, Repository.id == repository_id)
        )
        if not db_obj:
            return False

        self.db.delete(db_obj)
        self.db.commit()
        return True
