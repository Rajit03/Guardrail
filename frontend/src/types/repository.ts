export interface Repository {
  id: string;
  user_id: string;
  name: string;
  url: string;
  provider: string;
  default_branch: string;
  description?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_scan_at?: string;
  findings_count: number;
  last_scan_status?: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  asset_type?: string;
  asset_criticality?: string;
  exposure?: string;
}

export interface RepositoryCreate {
  name: string;
  url: string;
  provider?: string;
  default_branch?: string;
  description?: string;
}

export interface RepositoryUpdate {
  name?: string;
  description?: string;
  default_branch?: string;
  is_active?: boolean;
}

export interface RepositoryListResponse {
  repositories: Repository[];
}
