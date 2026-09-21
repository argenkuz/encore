import {
  useEffect,
  useState,
  type FormEvent,
} from "react";

import {
  createFilter,
  updateFilter,
  getManufacturers,
  getModels,
  getBadges,
} from "../api/client";

import type {
  Filter,
  FilterCreate,
  FilterUpdate,
} from "../types/filter";


interface FilterFormProps {
  telegramId: number;

  filter?: Filter | null;

  onSaved: () => void;

  onCancel: () => void;
}


interface CatalogItem {
  name: string;
  count?: number | null;
}


/* =========================================================
   CONSTANTS
   ========================================================= */

const YEARS = Array.from(
  {
    length: 30,
  },
  (_, index) => 2026 - index,
);


const MONTHS = Array.from(
  {
    length: 12,
  },
  (_, index) => index + 1,
);


const PRICE_PRESETS = [
  500,
  1000,
  1500,
  2000,
  2500,
  3000,
  4000,
  5000,
];


const MILEAGE_PRESETS = [
  30000,
  50000,
  70000,
  90000,
  120000,
  150000,
  200000,
];


const FUEL_TYPES = [
  {
    value: "",
    label: "Любое топливо",
  },
  {
    value: "가솔린",
    label: "Бензин",
  },
  {
    value: "디젤",
    label: "Дизель",
  },
  {
    value: "하이브리드",
    label: "Гибрид",
  },
  {
    value: "전기",
    label: "Электро",
  },
  {
    value: "LPG",
    label: "LPG",
  },
];


/* =========================================================
   COMPONENT
   ========================================================= */

export default function FilterForm({
  telegramId,
  filter,
  onSaved,
  onCancel,
}: FilterFormProps) {

  const isEditing = Boolean(filter);


  /* =======================================================
     FORM STATE
     ======================================================= */

  const [name, setName] = useState(
    filter?.name ?? "",
  );


  const [manufacturer, setManufacturer] =
    useState(
      filter?.manufacturer ?? "",
    );


  const [model, setModel] =
    useState(
      filter?.model ?? "",
    );


  const [badge, setBadge] =
    useState(
      filter?.badge ?? "",
    );


  const [yearFrom, setYearFrom] =
    useState(
      filter?.year_from
        ? String(filter.year_from)
        : "",
    );


  const [monthFrom, setMonthFrom] =
    useState(
      filter?.month_from
        ? String(filter.month_from)
        : "",
    );


  const [yearTo, setYearTo] =
    useState(
      filter?.year_to
        ? String(filter.year_to)
        : "",
    );


  const [monthTo, setMonthTo] =
    useState(
      filter?.month_to
        ? String(filter.month_to)
        : "",
    );


  const [priceFrom, setPriceFrom] =
    useState(
      filter?.price_from
        ? String(filter.price_from)
        : "",
    );


  const [priceTo, setPriceTo] =
    useState(
      filter?.price_to
        ? String(filter.price_to)
        : "",
    );


  const [mileageTo, setMileageTo] =
    useState(
      filter?.mileage_to
        ? String(filter.mileage_to)
        : "",
    );


  const [fuelType, setFuelType] =
    useState(
      filter?.fuel_type ?? "",
    );


  /* =======================================================
     CATALOG STATE
     ======================================================= */

  const [
    manufacturers,
    setManufacturers,
  ] = useState<CatalogItem[]>([]);


  const [
    models,
    setModels,
  ] = useState<CatalogItem[]>([]);


  const [
    badges,
    setBadges,
  ] = useState<CatalogItem[]>([]);


  const [
    loadingManufacturers,
    setLoadingManufacturers,
  ] = useState(false);


  const [
    loadingModels,
    setLoadingModels,
  ] = useState(false);


  const [
    loadingBadges,
    setLoadingBadges,
  ] = useState(false);


  /* =======================================================
     UI STATE
     ======================================================= */

  const [
    saving,
    setSaving,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState<string | null>(null);


  /* =======================================================
     LOAD MANUFACTURERS
     ======================================================= */

  useEffect(() => {

    let cancelled = false;


    async function loadManufacturers() {

      try {

        setLoadingManufacturers(true);


        const data =
          await getManufacturers();


        if (!cancelled) {

          setManufacturers(data);

        }

      } catch (err) {

        console.error(err);


        if (!cancelled) {

          setError(
            "Не удалось загрузить каталог автомобилей.",
          );

        }

      } finally {

        if (!cancelled) {

          setLoadingManufacturers(false);

        }

      }
    }


    loadManufacturers();


    return () => {

      cancelled = true;

    };

  }, []);


  /* =======================================================
     LOAD MODELS
     ======================================================= */

  useEffect(() => {

    if (!manufacturer) {

      setModels([]);

      return;

    }


    let cancelled = false;


    async function loadModels() {

      try {

        setLoadingModels(true);


        const data =
          await getModels(
            manufacturer,
          );


        if (!cancelled) {

          setModels(data);

        }

      } catch (err) {

        console.error(err);


        if (!cancelled) {

          setModels([]);

          setError(
            "Не удалось загрузить модели.",
          );

        }

      } finally {

        if (!cancelled) {

          setLoadingModels(false);

        }

      }

    }


    loadModels();


    return () => {

      cancelled = true;

    };

  }, [manufacturer]);


  /* =======================================================
     LOAD BADGES
     ======================================================= */

  useEffect(() => {

    if (
      !manufacturer ||
      !model
    ) {

      setBadges([]);

      return;

    }


    let cancelled = false;


    async function loadBadges() {

      try {

        setLoadingBadges(true);


        const data =
          await getBadges(
            manufacturer,
            model,
          );


        if (!cancelled) {

          setBadges(data);

        }

      } catch (err) {

        console.error(err);


        if (!cancelled) {

          setBadges([]);

          setError(
            "Не удалось загрузить комплектации.",
          );

        }

      } finally {

        if (!cancelled) {

          setLoadingBadges(false);

        }

      }

    }


    loadBadges();


    return () => {

      cancelled = true;

    };

  }, [
    manufacturer,
    model,
  ]);


  /* =======================================================
     MANUFACTURER CHANGE
     ======================================================= */

  function handleManufacturerChange(
    value: string,
  ) {

    setManufacturer(value);

    setModel("");
    setBadge("");

    setModels([]);
    setBadges([]);

    setError(null);
  }


  /* =======================================================
     MODEL CHANGE
     ======================================================= */

  function handleModelChange(
    value: string,
  ) {

    setModel(value);

    setBadge("");

    setBadges([]);

    setError(null);
  }


  /* =======================================================
     PRICE PRESET
     ======================================================= */

  function handlePricePreset(
    value: number,
  ) {

    setPriceTo(
      String(value),
    );
  }


  /* =======================================================
     MILEAGE PRESET
     ======================================================= */

  function handleMileagePreset(
    value: number,
  ) {

    setMileageTo(
      String(value),
    );
  }


  /* =======================================================
     SUBMIT
     ======================================================= */

  async function handleSubmit(
    event: FormEvent,
  ) {

    event.preventDefault();


    setError(null);


    if (!name.trim()) {

      setError(
        "Введите название фильтра.",
      );

      return;
    }


    try {

      setSaving(true);


      if (
        isEditing &&
        filter
      ) {

        const data: FilterUpdate = {

          name:
            name.trim(),

          manufacturer:
            manufacturer || null,

          model:
            model || null,

          badge:
            badge || null,

          year_from:
            yearFrom
              ? Number(yearFrom)
              : null,

          month_from:
            monthFrom
              ? Number(monthFrom)
              : null,

          year_to:
            yearTo
              ? Number(yearTo)
              : null,

          month_to:
            monthTo
              ? Number(monthTo)
              : null,

          price_from:
            priceFrom
              ? Number(priceFrom)
              : null,

          price_to:
            priceTo
              ? Number(priceTo)
              : null,

          mileage_from:
            null,

          mileage_to:
            mileageTo
              ? Number(mileageTo)
              : null,

          fuel_type:
            fuelType || null,

          transmission:
            null,

          region:
            null,
        };


        await updateFilter(
          filter.id,
          telegramId,
          data,
        );

      } else {

        const data: FilterCreate = {

          telegram_id:
            telegramId,

          name:
            name.trim(),

          manufacturer:
            manufacturer || null,

          model_group:
            null,

          model:
            model || null,

          badge:
            badge || null,

          year_from:
            yearFrom
              ? Number(yearFrom)
              : null,

          month_from:
            monthFrom
              ? Number(monthFrom)
              : null,

          year_to:
            yearTo
              ? Number(yearTo)
              : null,

          month_to:
            monthTo
              ? Number(monthTo)
              : null,

          price_from:
            priceFrom
              ? Number(priceFrom)
              : null,

          price_to:
            priceTo
              ? Number(priceTo)
              : null,

          mileage_from:
            null,

          mileage_to:
            mileageTo
              ? Number(mileageTo)
              : null,

          fuel_type:
            fuelType || null,

          transmission:
            null,

          region:
            null,
        };


        await createFilter(data);

      }


      onSaved();

    } catch (err) {

      console.error(err);


      if (err instanceof Error) {

        setError(err.message);

      } else {

        setError(
          "Не удалось сохранить фильтр.",
        );

      }

    } finally {

      setSaving(false);

    }
  }


  /* =======================================================
     RENDER
     ======================================================= */

  return (

    <div className="filter-overlay">

      <div className="filter-modal">


        {/* HEADER */}

        <div className="filter-modal-header">

          <div>

            <h2>
              {isEditing
                ? "Редактировать фильтр"
                : "Новый фильтр"}
            </h2>

            <p>
              Настройте параметры поиска
              автомобиля на Encar
            </p>

          </div>


          <button
            type="button"
            className="modal-close"
            onClick={onCancel}
          >
            ×
          </button>

        </div>


        {/* ERROR */}

        {error && (

          <div className="form-error">
            {error}
          </div>

        )}


        {/* FORM */}

        <form
          className="filter-form"
          onSubmit={handleSubmit}
        >


          {/* NAME */}

          <div className="field">

            <label>
              Название фильтра
            </label>

            <input
              type="text"
              value={name}
              onChange={(event) =>
                setName(
                  event.target.value,
                )
              }
              placeholder="Например: Kia K5 Hybrid"
            />

          </div>


          {/* MANUFACTURER */}

          <div className="field">

            <label>
              Марка
            </label>


            <select
              value={manufacturer}
              onChange={(event) =>
                handleManufacturerChange(
                  event.target.value,
                )
              }
              disabled={
                loadingManufacturers
              }
            >

              <option value="">

                {loadingManufacturers
                  ? "Загрузка..."
                  : "Выберите марку"}

              </option>


              {manufacturers.map(
                (item) => (

                  <option
                    key={item.name}
                    value={item.name}
                  >
                    {item.name}
                  </option>

                ),
              )}

            </select>

          </div>


          {/* MODEL */}

          <div className="field">

            <label>
              Модель
            </label>


            <select
              value={model}
              onChange={(event) =>
                handleModelChange(
                  event.target.value,
                )
              }
              disabled={
                !manufacturer ||
                loadingModels
              }
            >

              <option value="">

                {loadingModels
                  ? "Загрузка..."
                  : !manufacturer
                    ? "Сначала выберите марку"
                    : "Выберите модель"}

              </option>


              {models.map(
                (item) => (

                  <option
                    key={item.name}
                    value={item.name}
                  >
                    {item.name}
                  </option>

                ),
              )}

            </select>

          </div>


          {/* BADGE */}

          <div className="field">

            <label>
              Комплектация
            </label>


            <select
              value={badge}
              onChange={(event) =>
                setBadge(
                  event.target.value,
                )
              }
              disabled={
                !model ||
                loadingBadges
              }
            >

              <option value="">

                {loadingBadges
                  ? "Загрузка..."
                  : !model
                    ? "Сначала выберите модель"
                    : "Любая комплектация"}

              </option>


              {badges.map(
                (item) => (

                  <option
                    key={item.name}
                    value={item.name}
                  >
                    {item.name}
                  </option>

                ),
              )}

            </select>

          </div>


          {/* YEARS */}

          <div className="field">

            <label>
              Год выпуска
            </label>


            <div className="field-row">

              <select
                value={yearFrom}
                onChange={(event) =>
                  setYearFrom(
                    event.target.value,
                  )
                }
              >

                <option value="">
                  От
                </option>


                {YEARS.map(
                  (year) => (

                    <option
                      key={year}
                      value={year}
                    >
                      {year}
                    </option>

                  ),
                )}

              </select>


              <select
                value={yearTo}
                onChange={(event) =>
                  setYearTo(
                    event.target.value,
                  )
                }
              >

                <option value="">
                  До
                </option>


                {YEARS.map(
                  (year) => (

                    <option
                      key={year}
                      value={year}
                    >
                      {year}
                    </option>

                  ),
                )}

              </select>

            </div>

          </div>


          {/* MONTHS */}

          <div className="field">

            <label>
              Месяц выпуска
            </label>


            <div className="field-row">

              <select
                value={monthFrom}
                onChange={(event) =>
                  setMonthFrom(
                    event.target.value,
                  )
                }
              >

                <option value="">
                  От
                </option>


                {MONTHS.map(
                  (month) => (

                    <option
                      key={month}
                      value={month}
                    >
                      {month}
                    </option>

                  ),
                )}

              </select>


              <select
                value={monthTo}
                onChange={(event) =>
                  setMonthTo(
                    event.target.value,
                  )
                }
              >

                <option value="">
                  До
                </option>


                {MONTHS.map(
                  (month) => (

                    <option
                      key={month}
                      value={month}
                    >
                      {month}
                    </option>

                  ),
                )}

              </select>

            </div>

          </div>


          {/* PRICE */}

          <div className="field">

            <label>
              Цена, 만원
            </label>


            <div className="field-row">

              <input
                type="number"
                min="0"
                value={priceFrom}
                onChange={(event) =>
                  setPriceFrom(
                    event.target.value,
                  )
                }
                placeholder="От"
              />


              <input
                type="number"
                min="0"
                value={priceTo}
                onChange={(event) =>
                  setPriceTo(
                    event.target.value,
                  )
                }
                placeholder="До"
              />

            </div>


            <div className="preset-list">

              {PRICE_PRESETS.map(
                (price) => (

                  <button
                    type="button"
                    className="preset"
                    key={price}
                    onClick={() =>
                      handlePricePreset(
                        price,
                      )
                    }
                  >
                    {price}
                  </button>

                ),
              )}

            </div>

          </div>


          {/* MILEAGE */}

          <div className="field">

            <label>
              Максимальный пробег, км
            </label>


            <input
              type="number"
              min="0"
              value={mileageTo}
              onChange={(event) =>
                setMileageTo(
                  event.target.value,
                )
              }
              placeholder="Например: 90000"
            />


            <div className="preset-list">

              {MILEAGE_PRESETS.map(
                (mileage) => (

                  <button
                    type="button"
                    className="preset"
                    key={mileage}
                    onClick={() =>
                      handleMileagePreset(
                        mileage,
                      )
                    }
                  >
                    {mileage.toLocaleString(
                      "ru-RU",
                    )}
                  </button>

                ),
              )}

            </div>

          </div>


          {/* FUEL */}

          <div className="field">

            <label>
              Топливо
            </label>


            <select
              value={fuelType}
              onChange={(event) =>
                setFuelType(
                  event.target.value,
                )
              }
            >

              {FUEL_TYPES.map(
                (fuel) => (

                  <option
                    key={fuel.value}
                    value={fuel.value}
                  >
                    {fuel.label}
                  </option>

                ),
              )}

            </select>

          </div>


          {/* ACTIONS */}

          <div className="form-actions">

            <button
              type="button"
              className="secondary-button"
              onClick={onCancel}
              disabled={saving}
            >
              Отмена
            </button>


            <button
              type="submit"
              className="primary-button"
              disabled={saving}
            >
              {saving
                ? "Сохранение..."
                : isEditing
                  ? "Сохранить изменения"
                  : "Создать фильтр"}
            </button>

          </div>

        </form>

      </div>

    </div>

  );
}