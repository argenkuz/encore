import {
  useEffect,
  useState,
  type ChangeEvent,
} from "react";

import type {
  Filter,
} from "../types/filter";

import {
  createFilter,
  deleteFilter,
  getFilters,
  updateFilter,
  getMonitorSettings,
  updateMonitorSettings,
} from "../api/client";

import FilterCard from "../components/FilterCard";


interface HomePageProps {
  telegramId: number;
  onCreateFilter: () => void;
  onEditFilter: (filter: Filter) => void;
}


const INTERVALS = [1, 2, 5, 10, 30, 60];


function formatInterval(minutes: number) {
  if (minutes === 60) return "1 час";
  return `${minutes} мин`;
}


function formatNextRun(value: string | null) {
  if (!value) return "—";

  const date = new Date(
    value.endsWith("Z") ? value : `${value}Z`,
  );

  if (Number.isNaN(date.getTime())) return "—";

  return date.toLocaleTimeString(
    "ru-RU",
    {
      hour: "2-digit",
      minute: "2-digit",
    },
  );
}


export default function HomePage({
  telegramId,
  onCreateFilter,
  onEditFilter,
}: HomePageProps) {
  const [filters, setFilters] = useState<Filter[]>([]);
  const [loading, setLoading] = useState(true);
  const [settingsLoading, setSettingsLoading] = useState(true);
  const [savingSettings, setSavingSettings] = useState(false);
  const [error, setError] = useState("");
  const [interval, setIntervalValue] = useState(5);
  const [monitorEnabled, setMonitorEnabled] = useState(true);
  const [nextRunAt, setNextRunAt] = useState<string | null>(null);

  async function loadFilters() {
    try {
      setError("");
      setLoading(true);
      const data = await getFilters(telegramId);
      setFilters(data);
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "Не удалось загрузить фильтры",
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadMonitorSettings() {
    try {
      setSettingsLoading(true);
      const data = await getMonitorSettings(telegramId);
      setMonitorEnabled(data.enabled);
      setIntervalValue(data.interval_minutes);
      setNextRunAt(data.next_run_at);
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "Не удалось загрузить настройки монитора",
      );
    } finally {
      setSettingsLoading(false);
    }
  }

  useEffect(() => {
    void Promise.all([
      loadFilters(),
      loadMonitorSettings(),
    ]);
  }, [telegramId]);

  async function handleToggle(filter: Filter) {
    try {
      setError("");

      const updated = await updateFilter(
        filter.id,
        telegramId,
        { enabled: !filter.enabled },
      );

      setFilters((current) =>
        current.map((item) =>
          item.id === updated.id
            ? updated
            : item,
        ),
      );
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "Не удалось изменить фильтр",
      );
    }
  }

  async function handleDelete(filter: Filter) {
    const confirmed = window.confirm(
      `Удалить фильтр «${filter.name}»?`,
    );

    if (!confirmed) return;

    try {
      setError("");
      await deleteFilter(filter.id, telegramId);

      setFilters((current) =>
        current.filter(
          (item) => item.id !== filter.id,
        ),
      );
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "Не удалось удалить фильтр",
      );
    }
  }

  async function handleIntervalChange(value: number) {
    if (value === interval || savingSettings) return;

    try {
      setError("");
      setSavingSettings(true);

      const data = await updateMonitorSettings(
        telegramId,
        { interval_minutes: value },
      );

      setIntervalValue(data.interval_minutes);
      setMonitorEnabled(data.enabled);
      setNextRunAt(data.next_run_at);
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "Не удалось изменить интервал",
      );
    } finally {
      setSavingSettings(false);
    }
  }

  async function handleMonitorToggle() {
    if (savingSettings || settingsLoading) return;

    try {
      setError("");
      setSavingSettings(true);

      const data = await updateMonitorSettings(
        telegramId,
        { enabled: !monitorEnabled },
      );

      setMonitorEnabled(data.enabled);
      setIntervalValue(data.interval_minutes);
      setNextRunAt(data.next_run_at);
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "Не удалось изменить состояние монитора",
      );
    } finally {
      setSavingSettings(false);
    }
  }

  function handleExport() {
    const payload = {
      version: 1,
      exported_at: new Date().toISOString(),
      filters,
    };

    const blob = new Blob(
      [JSON.stringify(payload, null, 2)],
      { type: "application/json" },
    );

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "encar-monitor-filters.json";
    link.click();

    URL.revokeObjectURL(url);
  }

  async function handleImport(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    try {
      const text = await file.text();
      const payload = JSON.parse(text);

      if (!Array.isArray(payload?.filters)) {
        throw new Error(
          "Некорректный JSON: поле filters не найдено.",
        );
      }

      const imported = payload.filters as Filter[];

      // Import is intentionally additive. Existing filters are not
      // deleted or overwritten.
      for (const filter of imported) {
        if (!filter.name) continue;

        // Imported filters are created as new records.
        // This keeps the import additive and never mutates existing filters.
        const created = await createFilter({
          telegram_id: telegramId,
          name: filter.name,
          enabled: filter.enabled,
          manufacturer: filter.manufacturer,
          model_group: filter.model_group,
          model: filter.model,
          badge: filter.badge,
          year_from: filter.year_from,
          month_from: filter.month_from,
          year_to: filter.year_to,
          month_to: filter.month_to,
          price_from: filter.price_from,
          price_to: filter.price_to,
          mileage_from: filter.mileage_from,
          mileage_to: filter.mileage_to,
          fuel_type: filter.fuel_type,
          transmission: filter.transmission,
          region: filter.region,
        });

        setFilters((current) => [
          ...current,
          created,
        ]);
      }
    } catch (err) {
      console.error(err);
      setError(
        err instanceof Error
          ? err.message
          : "Не удалось импортировать JSON",
      );
    }
  }

  const activeFilters = filters.filter(
    (filter) => filter.enabled,
  ).length;

  return (
    <div className="page">
      <header className="app-header">
        <div className="app-logo">
          Encar <span>Монитор</span>
        </div>

        <button
          type="button"
          className={
            monitorEnabled
              ? "power-button active"
              : "power-button"
          }
          onClick={handleMonitorToggle}
          disabled={
            savingSettings ||
            settingsLoading
          }
          aria-label={
            monitorEnabled
              ? "Выключить монитор"
              : "Включить монитор"
          }
        >
          ⏻
        </button>
      </header>

      <main className="dashboard">
        <section
          className={
            monitorEnabled
              ? "monitor-status enabled"
              : "monitor-status disabled"
          }
        >
          <strong>
            {settingsLoading
              ? "Загрузка монитора..."
              : monitorEnabled
                ? "Монитор работает"
                : "Монитор выключен"}
          </strong>

          <span>
            {settingsLoading
              ? "Получаем настройки..."
              : monitorEnabled
                ? `Проверка каждые ${formatInterval(interval)}`
                : "Нажмите кнопку справа вверху"}
          </span>

          {monitorEnabled && !settingsLoading && (
            <small className="monitor-next-run">
              Следующая проверка: {formatNextRun(nextRunAt)}
            </small>
          )}
        </section>

        <section className="dashboard-card">
          <div className="section-title">
            КАК ЧАСТО ПРОВЕРЯТЬ
          </div>

          <div className="interval-list">
            {INTERVALS.map((value) => (
              <button
                type="button"
                key={value}
                className={
                  interval === value
                    ? "interval-button active"
                    : "interval-button"
                }
                onClick={() =>
                  void handleIntervalChange(value)
                }
                disabled={
                  savingSettings ||
                  settingsLoading
                }
              >
                {formatInterval(value)}
              </button>
            ))}
          </div>
        </section>

        <section className="dashboard-card filters-section">
          <div className="section-title">
            КАКИЕ МАШИНЫ ИСКАТЬ
          </div>

          {error && (
            <div className="dashboard-error">
              {error}
            </div>
          )}

          {loading ? (
            <div className="dashboard-message">
              Загрузка фильтров...
            </div>
          ) : filters.length === 0 ? (
            <div className="dashboard-message">
              Пока нет фильтров
            </div>
          ) : (
            <div className="filters-list">
              {filters.map((filter) => (
                <FilterCard
                  key={filter.id}
                  filter={filter}
                  onToggle={() =>
                    void handleToggle(filter)
                  }
                  onEdit={() =>
                    onEditFilter(filter)
                  }
                  onDelete={() =>
                    void handleDelete(filter)
                  }
                />
              ))}
            </div>
          )}

          <button
            type="button"
            className="add-filter-button"
            onClick={onCreateFilter}
          >
            + Добавить фильтр
          </button>

          <div className="import-export">
            <button
              type="button"
              className="outline-button"
              onClick={handleExport}
              disabled={loading || filters.length === 0}
            >
              ↓ Экспорт JSON
            </button>

            <label className="outline-button file-button">
              ↑ Импорт JSON
              <input
                type="file"
                accept="application/json,.json"
                onChange={(event) =>
                  void handleImport(event)
                }
                hidden
              />
            </label>
          </div>
        </section>

        <section className="dashboard-card telegram-card">
          <div className="section-title">
            TELEGRAM УВЕДОМЛЕНИЯ
          </div>

          <div className="telegram-status-row">
            <span className="telegram-status-dot" />
            <div>
              <strong>Уведомления подключены</strong>
              <span>
                Новые автомобили отправляются в Telegram
              </span>
            </div>
          </div>
        </section>

        <section className="dashboard-card journal-card">
          <div className="journal-header">
            <div className="section-title">
              СОСТОЯНИЕ
            </div>
            <span>
              {activeFilters} активных фильтра(ов)
            </span>
          </div>

          <div className="journal">
            <div>
              [INFO] Планировщик работает
            </div>
            <div>
              [INFO] Интервал пользователя: {formatInterval(interval)}
            </div>
            <div>
              [INFO] Активных фильтров: {activeFilters}
            </div>
            <div>
              [INFO] Следующая проверка: {formatNextRun(nextRunAt)}
            </div>
          </div>

          <div className="journal-actions">
            <button
              type="button"
              className="outline-button"
              onClick={() =>
                void Promise.all([
                  loadFilters(),
                  loadMonitorSettings(),
                ])
              }
            >
              Обновить
            </button>

            <button
              type="button"
              className="outline-button"
              onClick={() => setError("")}
            >
              Очистить ошибки
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
