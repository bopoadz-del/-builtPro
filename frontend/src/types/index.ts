export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  conversations: string[];
  createdAt: string;
  updatedAt: string;
  color?: string;
}
