export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  isStreaming?: boolean;
  model?: string;
}

export interface TableData {
  sequences?: {
    [key: string]: {
      gene_symbol: string;
      [key: string]: any;
    };
  };
  [key: string]: any;
}

export interface ConnectionState {
  error: string | null;
  isConnected: boolean;
}

export interface Chat {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  authToken: string | null;
  user: {
    id: string;
    username: string;
  } | null;
}