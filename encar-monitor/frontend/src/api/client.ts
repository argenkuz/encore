import type {
  Filter,
  FilterCreate,
  FilterUpdate,
} from "../types/filter";


const API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

async function apiFetch(path: string, init?: RequestInit) {
  const response = await fetch(`${API_URL}${path}`, init);

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail || "Ошибка API");
  }

  return response;
}



/* =========================================================
   FILTERS
   ========================================================= */

export async function getFilters(
  telegramId: number,
): Promise<Filter[]> {
  const response = await apiFetch(
    `/api/filters?telegram_id=${telegramId}`,
  );

  if (!response.ok) {
    throw new Error(
      "Не удалось загрузить фильтры",
    );
  }

  return response.json();
}


export async function getFilter(
  filterId: number,
  telegramId: number,
): Promise<Filter> {
  const response = await apiFetch(
    `/api/filters/${filterId}?telegram_id=${telegramId}`,
  );

  if (!response.ok) {
    throw new Error(
      "Не удалось загрузить фильтр",
    );
  }

  return response.json();
}


export async function createFilter(
  data: FilterCreate,
): Promise<Filter> {
  const response = await apiFetch(
    `/api/filters`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(data),
    },
  );

  if (!response.ok) {
    const error =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      error?.detail ||
      "Не удалось создать фильтр",
    );
  }

  return response.json();
}


export async function updateFilter(
  filterId: number,
  telegramId: number,
  data: FilterUpdate,
): Promise<Filter> {
  const response = await apiFetch(
    `/api/filters/${filterId}?telegram_id=${telegramId}`,
    {
      method: "PATCH",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(data),
    },
  );

  if (!response.ok) {
    const error =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      error?.detail ||
      "Не удалось изменить фильтр",
    );
  }

  return response.json();
}


export async function deleteFilter(
  filterId: number,
  telegramId: number,
): Promise<void> {
  const response = await apiFetch(
    `/api/filters/${filterId}?telegram_id=${telegramId}`,
    {
      method: "DELETE",
    },
  );

  if (!response.ok) {
    const error =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      error?.detail ||
      "Не удалось удалить фильтр",
    );
  }
}


/* =========================================================
   CATALOG
   ========================================================= */

export interface CatalogItem {
  name: string;
  count?: number | null;
}


/**
 * Получить марки автомобилей.
 *
 * Марки берутся из SQLite.
 */
export async function getManufacturers(): Promise<
  CatalogItem[]
> {
  const response = await apiFetch(
    `/api/catalog/manufacturers`,
  );

  if (!response.ok) {
    throw new Error(
      "Не удалось загрузить марки автомобилей",
    );
  }

  return response.json();
}


/**
 * Получить модели выбранной марки.
 *
 * Backend при первом запросе получает их
 * с Encar и сохраняет в SQLite.
 */
export async function getModels(
  manufacturer: string,
): Promise<CatalogItem[]> {
  const params = new URLSearchParams();

  params.set(
    "manufacturer",
    manufacturer,
  );

  const response = await apiFetch(
    `/api/catalog/models?${params.toString()}`,
  );

  if (!response.ok) {
    const error =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      error?.detail ||
      "Не удалось загрузить модели",
    );
  }

  return response.json();
}


/**
 * Получить комплектации выбранной модели.
 *
 * Backend при первом запросе получает их
 * с Encar и сохраняет в SQLite.
 */
export async function getBadges(
  manufacturer: string,
  model: string,
): Promise<CatalogItem[]> {
  const params = new URLSearchParams();

  params.set(
    "manufacturer",
    manufacturer,
  );

  params.set(
    "model",
    model,
  );

  const response = await apiFetch(
    `/api/catalog/badges?${params.toString()}`,
  );

  if (!response.ok) {
    const error =
      await response
        .json()
        .catch(() => null);

    throw new Error(
      error?.detail ||
      "Не удалось загрузить комплектации",
    );
  }

  return response.json();
}

export interface MonitorSettings {
  enabled: boolean;
  interval_minutes: number;
  last_run_at: string | null;
  next_run_at: string | null;
}

export async function getMonitorSettings(
  telegramId: number,
): Promise<MonitorSettings> {
  const response = await apiFetch(
    `/api/settings/monitor?telegram_id=${telegramId}`,
  );

  return response.json();
}

export async function updateMonitorSettings(
  telegramId: number,
  data: {
    enabled?: boolean;
    interval_minutes?: number;
  },
): Promise<MonitorSettings> {
  const response = await apiFetch(
    `/api/settings/monitor?telegram_id=${telegramId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    },
  );

  return response.json();
}
