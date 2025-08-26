import { getPreferenceValues } from "@raycast/api";

type Prefs = {
  serverUrl?: string;
  apiToken?: string;
};

export function getServerConfig() {
  const raw = getPreferenceValues<Prefs>();
  const url = (raw.serverUrl ?? "http://127.0.0.1:8002").replace(/\/+$/, ""); // strip trailing /
  const token = raw.apiToken?.trim();
  return { url, token };
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { url, token } = getServerConfig();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(init.headers as Record<string, string> | undefined),
  };
  const res = await fetch(`${url}${path}`, { ...init, headers });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
  return (await res.json()) as T;
}