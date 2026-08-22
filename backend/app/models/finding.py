import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=True)
    line_number: Mapped[int] = mapped_column(Integer, nullable=True)
    scanner: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_id: Mapped[str] = mapped_column(String(255), nullable=True)
    evidence: Mapped[str] = mapped_column(Text, nullable=True)
    recommendation: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="OPEN", nullable=False, index=True)
    fingerprint: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    repository = relationship("Repository", back_populates="findings", lazy="raise")
    scan = relationship("Scan", back_populates="findings", lazy="raise")
