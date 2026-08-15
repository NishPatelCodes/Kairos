const TOKEN_KEY = "kairos.access";
const REFRESH_KEY = "kairos.refresh";

export const API_BASE = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

function endpoint(path: string) {
  return `${API_BASE}${path}`;
}

export function getAccessToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem(TOKEN_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(endpoint(path), { ...init, headers });
  if (response.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      headers.set("Authorization", `Bearer ${getAccessToken()}`);
      const retry = await fetch(endpoint(path), { ...init, headers });
      if (!retry.ok) throw await errorFrom(retry);
      if (retry.status === 204) return undefined as T;
      return retry.json() as Promise<T>;
    }
    clearTokens();
    if (!window.location.pathname.startsWith("/login") && !window.location.pathname.startsWith("/register")) {
      window.location.href = "/login";
    }
  }
  if (!response.ok) throw await errorFrom(response);
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

async function tryRefresh() {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  const response = await fetch(endpoint("/api/auth/refresh/"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!response.ok) return false;
  const data = await response.json();
  if (!data.access) return false;
  setTokens(data.access, data.refresh || refresh);
  return true;
}

async function errorFrom(response: Response) {
  try {
    const data = await response.json();
    const detail = data.detail || data.error || JSON.stringify(data);
    return new Error(typeof detail === "string" ? detail : "Request failed");
  } catch {
    return new Error(`Request failed (${response.status})`);
  }
}

export type SseHandler = (event: string, data: Record<string, unknown>) => void;

export async function streamChat(message: string, onEvent: SseHandler) {
  const token = getAccessToken();
  const response = await fetch(endpoint("/api/ai/chat/"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message }),
  });
  if (!response.ok || !response.body) {
    throw await errorFrom(response);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() || "";
    for (const part of parts) {
      const eventMatch = part.match(/^event: (.+)$/m);
      const dataMatch = part.match(/^data: (.+)$/m);
      if (!eventMatch || !dataMatch) continue;
      try {
        onEvent(eventMatch[1], JSON.parse(dataMatch[1]));
      } catch {
        /* ignore malformed chunk */
      }
    }
  }
}
