import api from './api';
import {
  DashboardSummaryResponse,
  DashboardRepositoriesResponse,
  DashboardFindingsPaginatedResponse,
  DashboardRiskTrendResponse,
  DashboardFindingFilters,
} from '../types';

export const dashboardService = {
  async getSummary(): Promise<DashboardSummaryResponse> {
    const res = await api.get<DashboardSummaryResponse>('/dashboard/summary');
    return res.data;
  },

  async getRepositories(): Promise<DashboardRepositoriesResponse> {
    const res = await api.get<DashboardRepositoriesResponse>('/dashboard/repositories');
    return res.data;
  },

  async getFindings(filters: DashboardFindingFilters = {}): Promise<DashboardFindingsPaginatedResponse> {
    const params = new URLSearchParams();
    if (filters.repository_id) params.append('repository_id', filters.repository_id);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.type) params.append('type', filters.type);
    if (filters.status) params.append('status', filters.status);
    if (filters.scanner) params.append('scanner', filters.scanner);
    if (filters.search) params.append('search', filters.search);
    if (filters.page) params.append('page', filters.page.toString());
    if (filters.page_size) params.append('page_size', filters.page_size.toString());
    if (filters.sort_by) params.append('sort_by', filters.sort_by);

    const res = await api.get<DashboardFindingsPaginatedResponse>(`/dashboard/findings?${params.toString()}`);
    return res.data;
  },

  async getRiskTrend(): Promise<DashboardRiskTrendResponse> {
    const res = await api.get<DashboardRiskTrendResponse>('/dashboard/risk-trend');
    return res.data;
  },
};

export default dashboardService;
