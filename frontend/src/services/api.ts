import { apiFetch } from '../lib/api';

interface SendChatMessageParams {
  message: string;
  project_id?: string;
  use_internet?: boolean;
  attachments?: { name: string; size: number; type: string }[];
}

interface ChatResponse {
  response?: string;
  reply?: string;
  message?: string;
  content?: string;
  intent?: Record<string, unknown>;
  project_id?: string;
  citations?: Array<{
    document_id: string;
    document_name: string;
    snippet: string;
    relevance_score: number;
    page?: number;
  }>;
  confidence?: number;
  context_docs_count?: number;
}

const apiService = {
  async sendChatMessage(params: SendChatMessageParams): Promise<ChatResponse> {
    const response = await apiFetch('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        message: params.message,
        project_id: params.project_id,
      }),
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.status}`);
    }

    return response.json();
  },
};

export default apiService;
