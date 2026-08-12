import api from './api';
import { Scan, Finding, FindingListResponse, FindingFilters } from '../types';

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

    const response = await api.get<FindingListResponse>('/findings', { params });
    return response.data.findings;
  },

  async getFinding(findingId: string): Promise<Finding> {
    const response = await api.get<Finding>(`/findings/${findingId}`);
    return response.data;
  }
};

export default { scanService, findingService };
