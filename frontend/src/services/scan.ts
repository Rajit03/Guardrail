import api from './api';
import {
  Scan,
  Finding,
  FindingListResponse,
  FindingFilters,
  RiskAssessment,
  RepositoryRecalculateResponse
} from '../types';

export const scanService = {
  async scanRepository(repositoryId: string): Promise<Scan> {
    const response = await api.post<Scan>(`/repositories/${repositoryId}/scan`);
    return response.data;
  },

  async getScan(scanId: string): Promise<Scan> {
    const response = await api.get<Scan>(`/scans/${scanId}`);
    return response.data;
  },

  async getScanFindings(scanId: string): Promise<Finding[]> {
    const response = await api.get<FindingListResponse>(`/scans/${scanId}/findings`);
    return response.data.findings;
  }
};

export const findingService = {
  async getFindings(filters?: FindingFilters): Promise<Finding[]> {
    const params: Record<string, string> = {};
    if (filters?.repository_id) params.repository_id = filters.repository_id;
    if (filters?.severity) params.severity = filters.severity;
    if (filters?.type) params.type = filters.type;
    if (filters?.status) params.status = filters.status;
    if (filters?.risk_level) params.risk_level = filters.risk_level;
    if (filters?.priority) params.priority = filters.priority;
    if (filters?.sort_by) params.sort_by = filters.sort_by;

    const response = await api.get<FindingListResponse>('/findings', { params });
    return response.data.findings;
  },

  async getFinding(findingId: string): Promise<Finding> {
    const response = await api.get<Finding>(`/findings/${findingId}`);
    return response.data;
  }
};

export const riskService = {
  async getFindingRisk(findingId: string): Promise<RiskAssessment> {
    const response = await api.get<RiskAssessment>(`/findings/${findingId}/risk`);
    return response.data;
  },

  async recalculateFindingRisk(findingId: string): Promise<RiskAssessment> {
    const response = await api.post<RiskAssessment>(`/findings/${findingId}/risk/recalculate`);
    return response.data;
  },

  async recalculateRepositoryRisks(repositoryId: string): Promise<RepositoryRecalculateResponse> {
    const response = await api.post<RepositoryRecalculateResponse>(`/repositories/${repositoryId}/risk/recalculate`);
    return response.data;
  }
};

export default { scanService, findingService, riskService };
