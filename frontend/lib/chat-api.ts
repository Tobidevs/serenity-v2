export type Denomination =
  | "catholic"
  | "orthodox"
  | "reformed"
  | "anglican"
  | "lutheran";

export type AgentMode = "academic" | "devotional";

export interface ChatRequest {
  message: string;
  denomination: Denomination;
  mode: AgentMode;
  thread_id?: string;
}

export interface ChatResponse {
  thread_id: string;
  answer: string;
  sources: string[];
  scripture_references: string[];
  mode: AgentMode;
  denomination_notes: string;
}

const DEFAULT_BACKEND_URL = "http://localhost:8000";

function getBackendUrl(): string {
  const configuredUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? DEFAULT_BACKEND_URL;
  return configuredUrl.replace(/\/+$/, "");
}

export async function postChat(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${getBackendUrl()}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const failureText = await response.text();
    throw new Error(failureText || `Chat request failed with status ${response.status}`);
  }

  const data = (await response.json()) as ChatResponse;
  return data;
}