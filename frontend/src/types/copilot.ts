export interface RelatedFindingItem {
  id: string;
  title: string;
  severity: string;
  risk_score: number;
  priority: string;
  type: string;
  file_path?: string | null;
  package_name?: string | null;
  vulnerability_id?: string | null;
}

export interface CopilotChatRequest {
  message: string;
  repository_id?: string | null;
  finding_id?: string | null;
  scan_id?: string | null;
}

export interface CopilotChatResponse {
  answer: string;
  recommended_actions: string[];
  related_findings: RelatedFindingItem[];
  context_summary?: {
    intent?: string;
    findings_count?: number;
    overall_score?: number;
    fallback?: boolean;
  } | null;
  model_used: string;
}

export interface CopilotHealthResponse {
  status: 'HEALTHY' | 'UNAVAILABLE' | 'MODEL_MISSING' | 'UNREACHABLE' | 'TIMEOUT' | 'ERROR' | string;
  reachable: boolean;
  model_available: boolean;
  model_name: string;
  message: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'copilot';
  text: string;
  recommended_actions?: string[];
  related_findings?: RelatedFindingItem[];
  model_used?: string;
  timestamp: string;
  isFallback?: boolean;
}
