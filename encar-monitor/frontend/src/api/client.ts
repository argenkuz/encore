import type {
  Filter,
  FilterCreate,
  FilterUpdate,
} from "../types/filter";

const API_URL = (
  import.meta.env.VITE_API_URL ||
  `http://${window.location.hostname}:8000`
).replace(/\/$/, "");

const REQUEST_TIMEOUT_MS = 15000;

function getApiUrl(path: string): string {
  return `${API_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

async function fetchWithTimeout(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  const controller = new AbortController();
  const timeout = window.setTimeout(
    () => controller.abort(),
    REQUEST_TIMEOUT_MS,
  );

  try {
    return await fetch(input, {
      ...init,
      signal: init.signal ?? controller.signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(
        `Сервер не ответил за ${REQUEST_TIMEOUT_MS / 1000} сек. Проверьте backend и VITE_API_URL.`,
      );
    }

    if (error instanceof TypeError) {
      throw new Error(
        `Не удалось подключиться к API: ${getApiUrl(path)}. Проверьте backend/CORS.`,
      );
    }

    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string;
      };
    };
  }
}

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem("encar_access_token");

  if (token) {
    return { Authorization: `Bearer ${token}` };
  }

  const initData = window.Telegram?.WebApp?.initData;

  if (initData) {
    return { "X-Telegram-Init-Data": initData };
  }

  const devTelegramId = import.meta.env.VITE_DEV_TELEGRAM_ID;

  const isLocalhost =
    window.location.hostname === "localhost" ||
    window.location.hostname === "127.0.0.1";

  if (import.meta.env.DEV && devTelegramId && isLocalhost) {
    return { "X-Dev-Telegram-Id": devTelegramId };
  }

  return {};
}

async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);

  Object.entries(getAuthHeaders()).forEach(([key, value]) => {
    headers.set(key, value);
  });

  const response = await fetchWithTimeout(getApiUrl(path), {
    ...init,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    if (response.status === 401) {
      localStorage.removeItem("encar_access_token");
    }

    throw new Error(
      error?.detail ||
        `Ошибка API: ${response.status} ${response.statusText}`,
    );
  }

  return response;
}

export interface CurrentUser {
  id: number;
  telegram_id: number | null;
  username: string | null;
  role: string;
  is_active: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    username: string | null;
    role: string;
    is_active: boolean;
  };
}

export async function login(username: string, password: string): Promise<AuthResponse> {
  const response = await fetchWithTimeout(getApiUrl("/api/auth/login"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.detail || "Не удалось войти");
  }

  localStorage.setItem("encar_access_token", data.access_token);
  return data;
}

export async function register(username: string, password: string, masterPassword: string): Promise<AuthResponse> {
  const response = await fetchWithTimeout(getApiUrl("/api/auth/register"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, master_password: masterPassword }),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(data?.detail || "Не удалось зарегистрироваться");
  }

  localStorage.setItem("encar_access_token", data.access_token);
  return data;
}

export function logout(): void {
  localStorage.removeItem("encar_access_token");
}

export async function getCurrentUser(): Promise<CurrentUser> {
  const response = await apiFetch("/api/users/me");
  return response.json();
}

export async function getFilters(): Promise<Filter[]> {
  const response = await apiFetch("/api/filters");
  return response.json();
}

export async function getFilter(filterId: number): Promise<Filter> {
  const response = await apiFetch(`/api/filters/${filterId}`);
  return response.json();
}

export async function createFilter(data: FilterCreate): Promise<Filter> {
  const response = await apiFetch("/api/filters", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return response.json();
}

export async function updateFilter(
  filterId: number,
  data: FilterUpdate,
): Promise<Filter> {
  const response = await apiFetch(`/api/filters/${filterId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return response.json();
}

export async function deleteFilter(filterId: number): Promise<void> {
  await apiFetch(`/api/filters/${filterId}`, {
    method: "DELETE",
  });
}

export interface CatalogItem {
  name: string;
  count?: number | null;
}

export async function getManufacturers(): Promise<CatalogItem[]> {
  const response = await apiFetch("/api/catalog/manufacturers");
  return response.json();
}

export async function getModels(
  manufacturer: string,
): Promise<CatalogItem[]> {
  const params = new URLSearchParams({ manufacturer });
  const response = await apiFetch(`/api/catalog/models?${params}`);
  return response.json();
}

export async function getBadges(
  manufacturer: string,
  model: string,
): Promise<CatalogItem[]> {
  const params = new URLSearchParams({ manufacturer, model });
  const response = await apiFetch(`/api/catalog/badges?${params}`);
  return response.json();
}


export interface TelegramRecipient {
  telegram_id: number;
  created_at: string;
}

export async function getTelegramRecipients(
  masterPassword: string,
): Promise<TelegramRecipient[]> {
  const response = await apiFetch("/api/telegram/recipients", {
    headers: {
      "X-Master-Password": masterPassword,
    },
  });
  return response.json();
}

export async function addTelegramRecipient(
  telegramId: number,
  masterPassword: string,
): Promise<TelegramRecipient> {
  const response = await apiFetch("/api/telegram/recipients", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Master-Password": masterPassword,
    },
    body: JSON.stringify({
      telegram_id: telegramId,
    }),
  });
  return response.json();
}

export async function deleteTelegramRecipient(
  telegramId: number,
  masterPassword: string,
): Promise<void> {
  await apiFetch("/api/telegram/recipients/" + telegramId, {
    method: "DELETE",
    headers: {
      "X-Master-Password": masterPassword,
    },
  });
}

export interface MonitorSettings {
  enabled: boolean;
  interval_minutes: number;
  last_run_at: string | null;
  next_run_at: string | null;
}

export async function getMonitorSettings(): Promise<MonitorSettings> {
  const response = await apiFetch("/api/settings/monitor");
  return response.json();
}

export async function updateMonitorSettings(
  data: {
    enabled?: boolean;
    interval_minutes?: number;
  },
): Promise<MonitorSettings> {
  const response = await apiFetch("/api/settings/monitor", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return response.json();
}
