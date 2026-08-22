import { RiskAssessment } from './risk';

export interface Scan {
  id: string;
  repository_id: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  total_findings: number;
  scan_summary?: Record<string, any>;
  created_at?: string;
}

export interface Finding {
  id: string;
  repository_id: string;
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
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED' | 'FALSE_POSITIVE';
  created_at: string;

  // Extended Vulnerability Fields
  package_name?: string;
  installed_version?: string;
  fixed_version?: string;
  vulnerability_id?: string;
  aliases?: string[];

  // Risk Engine Fields
  risk_score?: number;
  risk_level?: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  priority?: 'P0' | 'P1' | 'P2' | 'P3';
  risk_assessment?: RiskAssessment;
}

export interface FindingListResponse {
  findings: Finding[];
}

export interface FindingFilters {
  repository_id?: string;
  severity?: string;
  type?: string;
  status?: string;
  risk_level?: string;
  priority?: string;
  sort_by?: string;
}
