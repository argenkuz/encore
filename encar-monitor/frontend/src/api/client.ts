import type {
  Filter,
  FilterCreate,
  FilterUpdate,
} from "../types/filter";

const API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

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
  const initData = window.Telegram?.WebApp?.initData;

  if (initData) {
    return { "X-Telegram-Init-Data": initData };
  }

  const devTelegramId = import.meta.env.VITE_DEV_TELEGRAM_ID;

  if (import.meta.env.DEV && devTelegramId) {
    return { "X-Dev-Telegram-Id": devTelegramId };
  }

  return {};
}

async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);

  Object.entries(getAuthHeaders()).forEach(([key, value]) => {
    headers.set(key, value);
  });

  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Ошибка API");
  }

  return response;
}

export interface CurrentUser {
  id: number;
  telegram_id: number;
  username: string | null;
  role: string;
  is_active: boolean;
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
