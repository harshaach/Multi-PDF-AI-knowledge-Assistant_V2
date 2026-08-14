import type { QueryResponse, HealthResponse, UploadResult } from '@/types';

/**
 * Centralized FastAPI backend client.
 *
 * Base URL is set via VITE_FASTAPI_URL (defaults to http://localhost:8000).
 *
 * Endpoints:
 *   GET    /health     -> { status, documents_indexed, chunks }
 *   GET    /documents  -> { documents: string[] }
 *   POST   /upload     -> multipart "files" -> [{ filename, chunks_indexed }]
 *   POST   /query      -> { question, top_k } -> { answer, sources: string[] }
 */

const BASE = (import.meta.env.VITE_FASTAPI_URL ?? 'http://localhost:8000').replace(/\/$/, '');
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Request to ${path} failed (${res.status}). ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

export async function fetchDocuments(chatId: string): Promise<string[]> {
  const data = await request<{ documents: string[] }>(
    `/documents?chat_id=${chatId}`
  );

  return data.documents ?? [];
}

export async function uploadPdfs(
  files: File[],
  chatId: string,
): Promise<UploadResult[]> {

  const form = new FormData();

  for (const file of files) {
    form.append("files", file);
  }

  const response = await fetch(
    `${BASE}/upload?chat_id=${chatId}`,
    {
      method: "POST",
      body: form,
    }
  );

  const text = await response.text();

  if (!response.ok) {
    throw new Error(text);
  }

  return JSON.parse(text);
}

export async function queryKnowledgeBase(
  question: string,
  chatId: string,
  topK = 5,
): Promise<QueryResponse> {

  return request<QueryResponse>(
    `/query?chat_id=${chatId}`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        top_k: topK,
      }),
    }
  );
}
