export interface Scan {
  id: string;
  repository_id: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  started_at?: string;
  completed_at?: string;
  total_findings: number;
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
}

export interface FindingListResponse {
  findings: Finding[];
}

export interface FindingFilters {
  repository_id?: string;
  severity?: string;
  type?: string;
  status?: string;
}
