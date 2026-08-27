export interface DashboardFindingCounts {
  total: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  info: number;
  open: number;
  resolved: number;
}

export interface DashboardTypeCounts {
  secret: number;
  dependency: number;
}

export interface DashboardRepositoriesSummary {
  total: number;
  scanned: number;
  unscanned: number;
}

export interface DashboardScannerStatus {
  name: string;
  status: string;
  operational: boolean;
  version?: string;
  last_run_at?: string;
}

export interface DashboardPriorityFinding {
  id: string;
  repository_id: string;
  repository_name: string;
  scan_id: string;
  type: 'SECRET' | 'DEPENDENCY';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  title: string;
  description?: string;
  file_path?: string;
  line_number?: number;
  scanner: string;
  rule_id?: string;
  evidence?: string;
  recommendation?: string;
  status: string;
  package_name?: string;
  vulnerability_id?: string;
  risk_score: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  created_at: string;
}

export interface DashboardRecentFinding {
  id: string;
  repository_id: string;
  repository_name: string;
  scan_id: string;
  type: 'SECRET' | 'DEPENDENCY';
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  title: string;
  description?: string;
  file_path?: string;
  line_number?: number;
  scanner: string;
  rule_id?: string;
  status: string;
  package_name?: string;
  vulnerability_id?: string;
  risk_score: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  created_at: string;
}

export interface DashboardRecentScan {
  id: string;
  repository_id: string;
  repository_name: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
  total_findings: number;
  scanners: Record<string, any>;
  created_at: string;
}

export interface DashboardRiskTrendPoint {
  scan_id: string;
  timestamp: string;
  date: string;
  security_score: number;
  finding_count: number;
  repository_id: string;
  repository_name: string;
}

export interface DashboardImprovements {
  new_findings: number;
  resolved_findings: number;
  persistent_findings: number;
  score_change?: number;
  previous_score?: number;
}

export interface DashboardSummaryResponse {
  security_score: number;
  risk_level: string;
  rating: string;
  score_change?: number;
  findings: DashboardFindingCounts;
  types: DashboardTypeCounts;
  repositories: DashboardRepositoriesSummary;
  scanners: Record<string, DashboardScannerStatus>;
  priority_findings: DashboardPriorityFinding[];
  recent_findings: DashboardRecentFinding[];
  recent_scans: DashboardRecentScan[];
  risk_trend: DashboardRiskTrendPoint[];
  improvements: DashboardImprovements;
}

export interface DashboardRepositoryItem {
  id: string;
  name: string;
  url: string;
  provider: string;
  default_branch: string;
  primary_language: string;
  security_score: number;
  risk_level: string;
  rating: string;
  finding_counts: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
    total_open: number;
    total_resolved: number;
  };
  last_scan_at?: string;
  last_scan_status?: string;
  scans_count: number;
}

export interface DashboardRepositoriesResponse {
  repositories: DashboardRepositoryItem[];
  total: number;
}

export interface DashboardFindingsPaginatedResponse {
  findings: DashboardRecentFinding[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DashboardRiskTrendResponse {
  points: DashboardRiskTrendPoint[];
  total_scans: number;
}

export interface DashboardFindingFilters {
  repository_id?: string;
  severity?: string;
  type?: string;
  status?: string;
  scanner?: string;
  search?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
}
