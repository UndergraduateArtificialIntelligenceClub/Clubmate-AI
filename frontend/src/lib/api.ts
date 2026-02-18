/**
 * Typed client for all Clubmate FastAPI backend calls.
 * All requests are authenticated with the Discord Bearer token from NextAuth session.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(
  path: string,
  token: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }

  return res.json() as Promise<T>;
}

// ── Types ──────────────────────────────────────────────────────────────────

export interface StatusResponse {
  bot: string;
  rag: { status: string; document_chunks: number };
  google_connected: boolean;
  model: string;
  exec_role: string;
}

export interface ConfigResponse {
  exec_role_name: string;
  default_llm_model: string;
  meeting_summary_channel_id: string;
  whisper_mode: string;
  top_k_results: number;
  temperature: number;
  embedding_model: string;
  google_connected: boolean;
  discord_guild_id: string;
}

export interface ConfigUpdate {
  exec_role_name?: string;
  default_llm_model?: string;
  meeting_summary_channel_id?: string;
  whisper_mode?: string;
  top_k_results?: number;
  temperature?: number;
}

export interface GoogleStatus {
  connected: boolean;
  account_email: string | null;
}

export interface RagStatus {
  status: string;
  has_documents: boolean;
  chunk_count: number;
}

// ── API calls ──────────────────────────────────────────────────────────────

export const api = {
  status: (token: string) =>
    apiFetch<StatusResponse>("/status", token),

  config: {
    get: (token: string) =>
      apiFetch<ConfigResponse>("/config", token),

    update: (token: string, updates: ConfigUpdate) =>
      apiFetch<{ message: string; updated: string[] }>("/config", token, {
        method: "PATCH",
        body: JSON.stringify(updates),
      }),
  },

  google: {
    status: (token: string) =>
      apiFetch<GoogleStatus>("/google/status", token),

    uploadCredentials: (token: string, credentialsJson: string) =>
      apiFetch<{ message: string }>("/google/credentials", token, {
        method: "POST",
        body: JSON.stringify({ credentials_json: credentialsJson }),
      }),

    startAuth: (token: string) =>
      apiFetch<{ auth_url: string }>("/google/auth", token),

    disconnect: (token: string) =>
      apiFetch<{ message: string }>("/google/disconnect", token, {
        method: "DELETE",
      }),
  },

  rag: {
    status: (token: string) =>
      apiFetch<RagStatus>("/rag/status", token),

    ingestFile: async (token: string, file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch(`${API_URL}/rag/ingest/file`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || `Upload error ${res.status}`);
      }
      return res.json();
    },

    ingestGoogleDoc: (token: string, url: string) =>
      apiFetch<{ message: string }>("/rag/ingest/google-doc", token, {
        method: "POST",
        body: JSON.stringify({ url }),
      }),

    reset: (token: string) =>
      apiFetch<{ message: string }>("/rag/reset", token, { method: "DELETE" }),
  },
};
