import api from './api';
import {
  Repository,
  RepositoryCreatePayload,
  RepositoryUpdatePayload,
  RepositoryListResponse,
  MessageResponse,
} from '../types';

export const repositoryService = {
  async list(): Promise<Repository[]> {
    const response = await api.get<RepositoryListResponse>('/repositories');
    return response.data.repositories;
  },

  async get(id: string): Promise<Repository> {
    const response = await api.get<Repository>(`/repositories/${id}`);
    return response.data;
  },

  async create(payload: RepositoryCreatePayload): Promise<Repository> {
    const response = await api.post<Repository>('/repositories', payload);
    return response.data;
  },

  async update(id: string, payload: RepositoryUpdatePayload): Promise<Repository> {
    const response = await api.patch<Repository>(`/repositories/${id}`, payload);
    return response.data;
  },

  async remove(id: string): Promise<MessageResponse> {
    const response = await api.delete<MessageResponse>(`/repositories/${id}`);
    return response.data;
  },
};

export default repositoryService;
