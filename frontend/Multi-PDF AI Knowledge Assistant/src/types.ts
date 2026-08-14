export type PdfStatus = 'pending' | 'processing' | 'ready' | 'error';

export interface Pdf {
  id: string;
  name: string;
  size_bytes: number;
  status: PdfStatus;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export type MessageRole = 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  session_id: string;
  role: MessageRole;
  content: string;
  sources: string[] | null;
  created_at: string;
}

export interface QueryResponse {
  answer: string;
  sources: string[];
}

export interface HealthResponse {
  status: string;
  documents_indexed: number;
  chunks: number;
}

export interface UploadResult {
  filename: string;
  chunks_indexed: number;
}
