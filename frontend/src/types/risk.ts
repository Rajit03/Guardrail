export interface RiskFactors {
  severity: number;
  exploitability: number;
  exposure: number;
  asset_criticality: number;
  confidence: number;
}

export interface RiskAssessment {
  id?: string;
  finding_id: string;
  risk_score: number;
  risk_level: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  priority: 'P0' | 'P1' | 'P2' | 'P3';
  factors: RiskFactors;
  explanation?: string;
  recommended_action?: string;
}

export interface RepositoryRecalculateResponse {
  repository_id: string;
  findings_processed: number;
  assessments_created: number;
}
