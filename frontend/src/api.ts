import type {
  AnswerResponse,
  CorpusInfo,
  DemoExample,
  ServiceStatus,
} from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function parseError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") return payload.detail;
    if (payload?.detail?.message) return payload.detail.message;
    if (typeof payload?.message === "string") return payload.message;
    return JSON.stringify(payload);
  } catch {
    return `${response.status} ${response.statusText}`;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    throw new Error(await parseError(response));
  }
  return (await response.json()) as T;
}

export function fetchStatus(): Promise<ServiceStatus> {
  return request<ServiceStatus>("/api/status");
}

export function fetchExamples(): Promise<{ examples: DemoExample[] }> {
  return request<{ examples: DemoExample[] }>("/api/examples");
}

export function fetchCorpus(): Promise<CorpusInfo> {
  return request<CorpusInfo>("/api/corpus");
}

export function submitQuery(
  query: string,
  useLlm: boolean,
  topK: number,
): Promise<AnswerResponse> {
  return request<AnswerResponse>("/api/query", {
    method: "POST",
    body: JSON.stringify({ query, use_llm: useLlm, top_k: topK }),
  });
}
