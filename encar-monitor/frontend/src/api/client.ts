import type {
  Filter,
  FilterCreate,
  FilterUpdate,
} from "../types/filter";


const API_URL = "http://127.0.0.1:8000";


/* =========================================================
   FILTERS
   ========================================================= */

export async function getFilters(
  telegramId: number,
): Promise<Filter[]> {
  const response = await fetch(
    `${API_URL}/api/filters?telegram_id=${telegramId}`,
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
  const response = await fetch(
    `${API_URL}/api/filters/${filterId}?telegram_id=${telegramId}`,
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
  const response = await fetch(
    `${API_URL}/api/filters`,
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
  const response = await fetch(
    `${API_URL}/api/filters/${filterId}?telegram_id=${telegramId}`,
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
  const response = await fetch(
    `${API_URL}/api/filters/${filterId}?telegram_id=${telegramId}`,
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
  const response = await fetch(
    `${API_URL}/api/catalog/manufacturers`,
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

  const response = await fetch(
    `${API_URL}/api/catalog/models?${params.toString()}`,
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

  const response = await fetch(
    `${API_URL}/api/catalog/badges?${params.toString()}`,
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