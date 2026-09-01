import api from './api';
import {
  CopilotChatRequest,
  CopilotChatResponse,
  CopilotHealthResponse,
} from '../types/copilot';

export const copilotService = {
  async chat(payload: CopilotChatRequest): Promise<CopilotChatResponse> {
    const res = await api.post<CopilotChatResponse>('/copilot/chat', payload);
    return res.data;
  },

  async getHealth(): Promise<CopilotHealthResponse> {
    const res = await api.get<CopilotHealthResponse>('/copilot/health');
    return res.data;
  },

  async clearHistory(): Promise<{ message: string }> {
    const res = await api.post<{ message: string }>('/copilot/clear-history');
    return res.data;
  },
};

export default copilotService;
