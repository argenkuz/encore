import {
  useEffect,
  useState,
} from "react";

import type { Filter } from "../types/filter";

import {
  deleteFilter,
  getFilters,
  updateFilter,
} from "../api/client";

import FilterCard from "../components/FilterCard";


interface HomePageProps {
  telegramId: number;

  onCreateFilter: () => void;

  onEditFilter: (
    filter: Filter,
  ) => void;
}


const INTERVALS = [
  1,
  2,
  5,
  10,
  30,
  60,
];


export default function HomePage({
  telegramId,
  onCreateFilter,
  onEditFilter,
}: HomePageProps) {

  /* =====================================================
     STATE
     ===================================================== */

  const [
    filters,
    setFilters,
  ] = useState<Filter[]>([]);


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState("");


  /*
   * Пока интервал хранится только
   * в frontend.
   *
   * Следующим шагом подключим его
   * к APScheduler backend.
   */

  const [
    interval,
    setIntervalValue,
  ] = useState(5);


  /*
   * Пока это состояние интерфейса.
   *
   * Следующим шагом подключим его
   * к реальному scheduler.
   */

  const [
    monitorEnabled,
    setMonitorEnabled,
  ] = useState(true);


  /* =====================================================
     LOAD FILTERS
     ===================================================== */

  async function loadFilters() {
    try {
      setError("");

      setLoading(true);

      const data =
        await getFilters(
          telegramId,
        );

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


  /* =====================================================
     INITIAL LOAD
     ===================================================== */

  useEffect(() => {
    loadFilters();
  }, [telegramId]);


  /* =====================================================
     TOGGLE FILTER
     ===================================================== */

  async function handleToggle(
    filter: Filter,
  ) {
    try {

      setError("");

      const updated =
        await updateFilter(
          filter.id,
          telegramId,
          {
            enabled:
              !filter.enabled,
          },
        );


      setFilters(
        (current) =>
          current.map(
            (item) =>
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


  /* =====================================================
     DELETE FILTER
     ===================================================== */

  async function handleDelete(
    filter: Filter,
  ) {

    const confirmed =
      window.confirm(
        `Удалить фильтр «${filter.name}»?`,
      );


    if (!confirmed) {
      return;
    }


    try {

      setError("");

      await deleteFilter(
        filter.id,
        telegramId,
      );


      setFilters(
        (current) =>
          current.filter(
            (item) =>
              item.id !== filter.id,
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


  /* =====================================================
     CHANGE INTERVAL
     ===================================================== */

  function handleIntervalChange(
    value: number,
  ) {
    setIntervalValue(value);

    /*
     * Пока только frontend.
     *
     * Следующим шагом:
     *
     * PATCH /api/settings
     *
     * и backend изменит APScheduler.
     */
  }


  /* =====================================================
     TOGGLE MONITOR
     ===================================================== */

  function handleMonitorToggle() {
    setMonitorEnabled(
      (current) => !current,
    );

    /*
     * Пока только UI.
     *
     * Позже подключим к backend.
     */
  }


  /* =====================================================
     RENDER
     ===================================================== */

  return (
    <div className="page">

      {/* =================================================
          HEADER
          ================================================= */}

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
          onClick={
            handleMonitorToggle
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


      {/* =================================================
          DASHBOARD
          ================================================= */}

      <main className="dashboard">


        {/* ===============================================
            MONITOR STATUS
            =============================================== */}

        <section
          className={
            monitorEnabled
              ? "monitor-status enabled"
              : "monitor-status disabled"
          }
        >

          <strong>
            {monitorEnabled
              ? "Монитор работает"
              : "Монитор выключен"}
          </strong>


          <span>

            {monitorEnabled
              ? `Проверка каждые ${interval} ${
                  interval === 60
                    ? "час"
                    : "мин"
                }`
              : "Нажмите кнопку справа вверху"}

          </span>

        </section>


        {/* ===============================================
            INTERVAL
            =============================================== */}

        <section className="dashboard-card">

          <div className="section-title">
            КАК ЧАСТО ПРОВЕРЯТЬ
          </div>


          <div className="interval-list">

            {INTERVALS.map(
              (value) => (

                <button
                  type="button"
                  key={value}
                  className={
                    interval === value
                      ? "interval-button active"
                      : "interval-button"
                  }
                  onClick={() =>
                    handleIntervalChange(
                      value,
                    )
                  }
                >

                  {value === 60
                    ? "1 час"
                    : `${value} мин`}

                </button>

              ),
            )}

          </div>

        </section>


        {/* ===============================================
            FILTERS
            =============================================== */}

        <section className="dashboard-card filters-section">

          <div className="section-title">
            КАКИЕ МАШИНЫ ИСКАТЬ
          </div>


          {/* LOADING */}

          {loading && (
            <div className="dashboard-message">
              Загрузка фильтров...
            </div>
          )}


          {/* ERROR */}

          {error && (
            <div className="dashboard-error">
              {error}
            </div>
          )}


          {/* EMPTY */}

          {!loading &&
            !error &&
            filters.length === 0 && (

              <div className="dashboard-message">
                Пока нет фильтров
              </div>

            )}


          {/* FILTER LIST */}

          {!loading && (
            <div className="filters-list">

              {filters.map(
                (filter) => (

                  <FilterCard
                    key={filter.id}
                    filter={filter}

                    onToggle={() =>
                      handleToggle(
                        filter,
                      )
                    }

                    onEdit={() =>
                      onEditFilter(
                        filter,
                      )
                    }

                    onDelete={() =>
                      handleDelete(
                        filter,
                      )
                    }
                  />

                ),
              )}

            </div>
          )}


          {/* ADD FILTER */}

          <button
            type="button"
            className="add-filter-button"
            onClick={
              onCreateFilter
            }
          >
            + Добавить фильтр
          </button>


          {/* JSON */}

          <div className="import-export">

            <button
              type="button"
              className="outline-button"
              onClick={() => {
                /*
                 * Пока будет реализовано
                 * следующим шагом.
                 */
              }}
            >
              ↓ Экспорт JSON
            </button>


            <button
              type="button"
              className="outline-button"
              onClick={() => {
                /*
                 * Пока будет реализовано
                 * следующим шагом.
                 */
              }}
            >
              ↑ Импорт JSON
            </button>

          </div>

        </section>


        {/* ===============================================
            TELEGRAM
            =============================================== */}

        <section className="dashboard-card telegram-card">

          <div className="section-title">
            TELEGRAM УВЕДОМЛЕНИЯ
          </div>


          <button
            type="button"
            className="locked-setting"
            onClick={() => {
              /*
               * Настройки Telegram
               * подключим следующим шагом.
               */
            }}
          >
            🔒 Нажмите чтобы настроить
          </button>

        </section>


        {/* ===============================================
            JOURNAL
            =============================================== */}

        <section className="dashboard-card journal-card">

          <div className="journal-header">

            <div className="section-title">
              ЖУРНАЛ
            </div>

            <span>
              ▲
            </span>

          </div>


          <div className="journal">

            <div>
              [INFO] Монитор запущен...
            </div>

            <div>
              [INFO] Ожидание следующей проверки...
            </div>

            <div>
              [INFO] Активных фильтров:{" "}
              {
                filters.filter(
                  (filter) =>
                    filter.enabled,
                ).length
              }
            </div>

          </div>


          <div className="journal-actions">

            <button
              type="button"
              className="outline-button"
              onClick={
                loadFilters
              }
            >
              Обновить
            </button>


            <button
              type="button"
              className="outline-button"
              onClick={() => {
                /*
                 * Очистку журнала подключим,
                 * когда сделаем backend logs API.
                 */
              }}
            >
              Очистить
            </button>

          </div>

        </section>

      </main>

    </div>
  );
}