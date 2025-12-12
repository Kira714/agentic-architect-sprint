import axios from 'axios';
import { FoundryState } from './types';

const API_BASE = '/api';

export interface CreateProtocolRequest {
  user_query: string;
  user_intent?: string;
  max_iterations?: number;
}

export interface ApproveRequest {
  edited_draft?: string;
  feedback?: string;
}

export const api = {
  async createProtocol(request: CreateProtocolRequest) {
    const response = await axios.post(`${API_BASE}/protocols/create`, request);
    return response.data;
  },

  async getProtocolState(threadId: string): Promise<{ state: FoundryState }> {
    const response = await axios.get(`${API_BASE}/protocols/${threadId}/state`);
    return response.data;
  },

  async approveProtocol(threadId: string, request: ApproveRequest) {
    const response = await axios.post(
      `${API_BASE}/protocols/${threadId}/approve`,
      request
    );
    return response.data;
  },

  async listProtocols() {
    const response = await axios.get(`${API_BASE}/protocols`);
    return response.data;
  },
};





