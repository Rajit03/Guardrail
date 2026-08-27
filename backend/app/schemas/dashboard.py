import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class DashboardSummaryFindingCounts(BaseModel):
    total: int = 0
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    open: int = 0
    resolved: int = 0


class DashboardSummaryTypeCounts(BaseModel):
    secret: int = 0
    dependency: int = 0


class DashboardSummaryRepositories(BaseModel):
    total: int = 0
    scanned: int = 0
    unscanned: int = 0


class DashboardScannerStatus(BaseModel):
    name: str
    status: str
    operational: bool
    version: Optional[str] = None
    last_run_at: Optional[datetime] = None


class DashboardPriorityFinding(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    repository_name: str
    scan_id: uuid.UUID
    type: str
    severity: str
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    scanner: str
    rule_id: Optional[str] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None
    status: str
    package_name: Optional[str] = None
    vulnerability_id: Optional[str] = None
    risk_score: int
    risk_level: str
    priority: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardRecentFinding(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    repository_name: str
    scan_id: uuid.UUID
    type: str
    severity: str
    title: str
    description: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    scanner: str
    rule_id: Optional[str] = None
    status: str
    package_name: Optional[str] = None
    vulnerability_id: Optional[str] = None
    risk_score: int
    risk_level: str
    priority: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardRecentScan(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    repository_name: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    total_findings: int = 0
    scanners: Dict[str, Any] = {}
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DashboardRiskTrendPoint(BaseModel):
    scan_id: uuid.UUID
    timestamp: datetime
    date: str
    security_score: int
    finding_count: int
    repository_id: uuid.UUID
    repository_name: str


class DashboardImprovements(BaseModel):
    new_findings: int = 0
    resolved_findings: int = 0
    persistent_findings: int = 0
    score_change: Optional[int] = None
    previous_score: Optional[int] = None


class DashboardSummaryResponse(BaseModel):
    security_score: int
    risk_level: str
    rating: str
    score_change: Optional[int] = None
    findings: DashboardSummaryFindingCounts
    types: DashboardSummaryTypeCounts
    repositories: DashboardSummaryRepositories
    scanners: Dict[str, DashboardScannerStatus]
    priority_findings: List[DashboardPriorityFinding]
    recent_findings: List[DashboardRecentFinding]
    recent_scans: List[DashboardRecentScan]
    risk_trend: List[DashboardRiskTrendPoint]
    improvements: DashboardImprovements


class FindingSeverityCounts(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    total_open: int = 0
    total_resolved: int = 0


class DashboardRepositoryItem(BaseModel):
    id: uuid.UUID
    name: str
    url: str
    provider: str
    default_branch: str
    primary_language: str
    security_score: int
    risk_level: str
    rating: str
    finding_counts: FindingSeverityCounts
    last_scan_at: Optional[datetime] = None
    last_scan_status: Optional[str] = None
    scans_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class DashboardRepositoriesResponse(BaseModel):
    repositories: List[DashboardRepositoryItem]
    total: int


class DashboardFindingsPaginatedResponse(BaseModel):
    findings: List[DashboardRecentFinding]
    total: int
    page: int
    page_size: int
    total_pages: int


class DashboardRiskTrendResponse(BaseModel):
    points: List[DashboardRiskTrendPoint]
    total_scans: int
