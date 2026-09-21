import type { Filter } from "../types/filter";

interface FilterCardProps {
  filter: Filter;
  onToggle: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export default function FilterCard({
  filter,
  onToggle,
  onEdit,
  onDelete,
}: FilterCardProps) {
  function formatYear() {
    if (!filter.year_from && !filter.year_to) {
      return null;
    }

    const from = filter.year_from
      ? filter.month_from
        ? `${String(filter.month_from).padStart(2, "0")}.${filter.year_from}`
        : `${filter.year_from}`
      : "—";

    const to = filter.year_to
      ? filter.month_to
        ? `${String(filter.month_to).padStart(2, "0")}.${filter.year_to}`
        : `${filter.year_to}`
      : "—";

    return `${from} – ${to}`;
  }

  function formatPrice() {
    if (filter.price_from == null && filter.price_to == null) {
      return null;
    }

    const from =
      filter.price_from != null
        ? filter.price_from.toLocaleString("ru-RU")
        : "0";

    const to =
      filter.price_to != null
        ? filter.price_to.toLocaleString("ru-RU")
        : "∞";

    return `${from} – ${to}`;
  }

  function formatMileage() {
    if (filter.mileage_from == null && filter.mileage_to == null) {
      return null;
    }

    const from =
      filter.mileage_from != null
        ? filter.mileage_from.toLocaleString("ru-RU")
        : "0";

    const to =
      filter.mileage_to != null
        ? filter.mileage_to.toLocaleString("ru-RU")
        : "∞";

    return `${from} – ${to} км`;
  }

  const year = formatYear();
  const price = formatPrice();
  const mileage = formatMileage();

  const carName = [
    filter.manufacturer,
    filter.model_group,
    filter.model,
  ]
    .filter(Boolean)
    .join(" · ");

  return (
    <div
      className={`filter-card ${
        filter.enabled ? "" : "filter-card-disabled"
      }`}
    >
      <div className="filter-card-header">
        <div>
          <div className="filter-name">
            {filter.name}
          </div>

          {carName && (
            <div className="filter-car-name">
              {carName}
            </div>
          )}
        </div>

        <button
          type="button"
          className={`filter-toggle ${
            filter.enabled ? "active" : ""
          }`}
          onClick={onToggle}
          aria-label={
            filter.enabled
              ? "Выключить фильтр"
              : "Включить фильтр"
          }
        >
          <span />
        </button>
      </div>

      <div className="filter-tags">
        {year && (
          <span className="filter-tag">
            📅 {year}
          </span>
        )}

        {price && (
          <span className="filter-tag">
            💰 {price}
          </span>
        )}

        {mileage && (
          <span className="filter-tag">
            🛣 {mileage}
          </span>
        )}

        {filter.fuel_type && (
          <span className="filter-tag">
            ⛽ {filter.fuel_type}
          </span>
        )}

        {filter.badge && (
          <span className="filter-tag">
            {filter.badge}
          </span>
        )}

        {filter.transmission && (
          <span className="filter-tag">
            {filter.transmission}
          </span>
        )}

        {filter.region && (
          <span className="filter-tag">
            📍 {filter.region}
          </span>
        )}
      </div>

      <div className="filter-card-actions">
        <button
          type="button"
          className="filter-edit-button"
          onClick={onEdit}
        >
          ✎ Изменить
        </button>

        <button
          type="button"
          className="filter-delete-button"
          onClick={onDelete}
        >
          🗑 Удалить
        </button>
      </div>
    </div>
  );
}