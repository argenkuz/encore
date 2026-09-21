export interface Filter {
  id: number;
  user_id: number;

  name: string;
  enabled: boolean;

  manufacturer: string | null;
  model_group: string | null;
  model: string | null;
  badge: string | null;

  year_from: number | null;
  month_from: number | null;
  year_to: number | null;
  month_to: number | null;

  price_from: number | null;
  price_to: number | null;

  mileage_from: number | null;
  mileage_to: number | null;

  fuel_type: string | null;
  transmission: string | null;
  region: string | null;
}

export interface FilterCreate {
  telegram_id: number;

  name: string;

  manufacturer?: string | null;
  model_group?: string | null;
  model?: string | null;
  badge?: string | null;

  year_from?: number | null;
  month_from?: number | null;
  year_to?: number | null;
  month_to?: number | null;

  price_from?: number | null;
  price_to?: number | null;

  mileage_from?: number | null;
  mileage_to?: number | null;

  fuel_type?: string | null;
  transmission?: string | null;
  region?: string | null;
}

export interface FilterUpdate {
  name?: string;
  enabled?: boolean;

  manufacturer?: string | null;
  model_group?: string | null;
  model?: string | null;
  badge?: string | null;

  year_from?: number | null;
  month_from?: number | null;
  year_to?: number | null;
  month_to?: number | null;

  price_from?: number | null;
  price_to?: number | null;

  mileage_from?: number | null;
  mileage_to?: number | null;

  fuel_type?: string | null;
  transmission?: string | null;
  region?: string | null;
}