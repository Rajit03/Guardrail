import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Integer, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    severity_factor: Mapped[float] = mapped_column(Float, nullable=False, default=5.0)
    exploitability_factor: Mapped[float] = mapped_column(Float, nullable=False, default=0.4)
    exposure_factor: Mapped[float] = mapped_column(Float, nullable=False, default=0.4)
    asset_criticality_factor: Mapped[float] = mapped_column(Float, nullable=False, default=0.4)
    confidence_factor: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    explanation: Mapped[str] = mapped_column(Text, nullable=True)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=True)
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

    finding = relationship("Finding", back_populates="risk_assessment", lazy="raise")

    @property
    def factors(self) -> dict:
        return {
            "severity": self.severity_factor,
            "exploitability": self.exploitability_factor,
            "exposure": self.exposure_factor,
            "asset_criticality": self.asset_criticality_factor,
            "confidence": self.confidence_factor,
        }
