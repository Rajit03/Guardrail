import api from './api';
import {
  Repository,
  RepositoryCreate,
  RepositoryUpdate,
  RepositoryListResponse,
  MessageResponse
} from '../types';

export const repositoryService = {
  async getRepositories(): Promise<Repository[]> {
    const response = await api.get<RepositoryListResponse>('/repositories');
    return response.data.repositories;
  },

  async getRepository(id: string): Promise<Repository> {
    const response = await api.get<Repository>(`/repositories/${id}`);
    return response.data;
  },

  async createRepository(payload: RepositoryCreate): Promise<Repository> {
    const response = await api.post<Repository>('/repositories', payload);
    return response.data;
  },

  async updateRepository(id: string, payload: RepositoryUpdate): Promise<Repository> {
    const response = await api.patch<Repository>(`/repositories/${id}`, payload);
    return response.data;
  },

  async deleteRepository(id: string): Promise<MessageResponse> {
    const response = await api.delete<MessageResponse>(`/repositories/${id}`);
    return response.data;
  },

  async getRepositoryScans(id: string): Promise<import('../types').Scan[]> {
    const response = await api.get<import('../types').Scan[]>(`/repositories/${id}/scans`);
    return response.data;
  }
};

export default repositoryService;
