export interface User {
  id: string;
  name: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface MessageResponse {
  message: string;
}

export interface ApiError {
  detail: string | { msg: string; loc: string[] }[];
}

export interface Repository {
  id: string;
  name: string;
  url: string;
  provider: string;
  default_branch: string;
  description: string | null;
  is_active: boolean;
  last_scan_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RepositoryCreatePayload {
  name: string;
  url: string;
  provider: string;
  default_branch: string;
  description?: string;
}

export interface RepositoryUpdatePayload {
  name?: string;
  default_branch?: string;
  description?: string | null;
  is_active?: boolean;
}

export interface RepositoryListResponse {
  repositories: Repository[];
}
