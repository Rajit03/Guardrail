import api from './api';
import { User, AuthToken, RegisterPayload, LoginPayload, MessageResponse } from '../types';

export const authService = {
  async register(payload: RegisterPayload): Promise<MessageResponse> {
    const response = await api.post<MessageResponse>('/auth/register', payload);
    return response.data;
  },

  async login(payload: LoginPayload): Promise<AuthToken> {
    const response = await api.post<AuthToken>('/auth/login', payload);
    if (response.data.access_token) {
      localStorage.setItem('guardrail_token', response.data.access_token);
    }
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },

  logout(): void {
    localStorage.removeItem('guardrail_token');
  },

  getToken(): string | null {
    return localStorage.getItem('guardrail_token');
  }
};

export default authService;
