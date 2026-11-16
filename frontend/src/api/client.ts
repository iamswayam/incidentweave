import type {
  InvestigationResponse,
  InvestigationSummary,
  RepositorySummary,
} from "./types";
import { ApiError, type ApiErrorBody } from "./types";

export interface ApiSettings {
  apiBase: string;
  apiSecret: string;
}

function trimSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

export function resolveApiBase(settings: ApiSettings): string {
  const configured = settings.apiBase.trim();
  if (configured) return trimSlash(configured);

  const proxyPrefix = import.meta.env.VITE_API_PROXY_PREFIX;
  if (typeof proxyPrefix === "string" && proxyPrefix.trim()) {
    return trimSlash(proxyPrefix.trim());
  }

  const envBase = import.meta.env.VITE_API_BASE_URL;
  if (typeof envBase === "string" && envBase.trim()) {
    return trimSlash(envBase.trim());
  }

  return "http://localhost:8000";
}

function messageForStatus(status: number, payload: ApiErrorBody | null): string {
  const code = payload?.error?.code;
  const message = payload?.error?.message;

  if (status === 0) {
    return "Could not reach the API. Is the backend running?";
  }
  if (status === 401) {
    return "Unauthorized. Check the API secret in Settings.";
  }
  if (status === 404 && code === "repository_not_found") {
    return "That repository has not been ingested yet.";
  }
  if (status === 404) {
    return typeof message === "string" ? message : "The requested record was not found.";
  }
  if (status === 422) {
    return typeof message === "string" ? message : "The request could not be validated.";
  }
  if (status === 429) {
    return typeof message === "string"
      ? message
      : "Request limit exceeded. Try again in a minute.";
  }
  if (status === 500 || status === 502) {
    return "The service had a problem. Check the backend logs.";
  }
  return typeof message === "string" ? message : "The request could not be completed.";
}

export async function apiFetch<T>(
  settings: ApiSettings,
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const base = resolveApiBase(settings);
  const url = `${base}${path.startsWith("/") ? path : `/${path}`}`;
  const headers = new Headers(init.headers || {});

  if (settings.apiSecret.trim()) {
    headers.set("X-API-Secret", settings.apiSecret.trim());
  }
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  let response: Response;
  try {
    response = await fetch(url, { ...init, headers });
  } catch {
    throw new ApiError(0, messageForStatus(0, null));
  }

  let payload: unknown = null;
  if (response.status !== 204) {
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const body = (payload && typeof payload === "object" ? payload : null) as ApiErrorBody | null;
    throw new ApiError(
      response.status,
      messageForStatus(response.status, body),
      body?.error?.code ?? null,
    );
  }

  return payload as T;
}

export function listRepositories(settings: ApiSettings) {
  return apiFetch<RepositorySummary[]>(settings, "/repositories");
}

export function listInvestigations(
  settings: ApiSettings,
  params: { repository_name?: string; limit?: number; before_id?: number } = {},
) {
  const query = new URLSearchParams();
  if (params.repository_name) query.set("repository_name", params.repository_name);
  if (params.limit != null) query.set("limit", String(params.limit));
  if (params.before_id != null) query.set("before_id", String(params.before_id));
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return apiFetch<InvestigationSummary[]>(settings, `/investigations${suffix}`);
}

export function getInvestigation(settings: ApiSettings, id: number) {
  return apiFetch<InvestigationResponse>(settings, `/investigations/${id}`);
}

export function createInvestigation(
  settings: ApiSettings,
  body: {
    repository_name: string;
    query: string;
    limit: number;
  },
) {
  return apiFetch<InvestigationResponse>(settings, "/investigations", {
    method: "POST",
    body: JSON.stringify({ ...body, debug: true }),
  });
}

export async function checkHealth(settings: ApiSettings): Promise<boolean> {
  try {
    const base = resolveApiBase(settings);
    const response = await fetch(`${base}/health`);
    return response.ok;
  } catch {
    return false;
  }
}
