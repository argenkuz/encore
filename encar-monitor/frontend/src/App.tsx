import { useState } from "react";

import HomePage from "./pages/HomePage";
import FilterForm from "./components/FilterForm";

import type { Filter } from "./types/filter";


type Page =
  | "home"
  | "create"
  | "edit";


function App() {
  /*
   * Временный Telegram ID для локальной разработки.
   *
   * Это твой реальный Telegram ID.
   *
   * Позже заменим его на Telegram Mini App initData,
   * чтобы ID определялся автоматически.
   */

  const telegramId = 1100664785;


  const [
    page,
    setPage,
  ] = useState<Page>("home");


  const [
    editingFilter,
    setEditingFilter,
  ] = useState<Filter | null>(null);


  /* =====================================================
     CREATE FILTER
     ===================================================== */

  function handleCreateFilter() {
    setEditingFilter(null);

    setPage("create");
  }


  /* =====================================================
     EDIT FILTER
     ===================================================== */

  function handleEditFilter(
    filter: Filter,
  ) {
    setEditingFilter(filter);

    setPage("edit");
  }


  /* =====================================================
     BACK
     ===================================================== */

  function handleBack() {
    setEditingFilter(null);

    setPage("home");
  }


  /* =====================================================
     SAVED
     ===================================================== */

  function handleSaved() {
    setEditingFilter(null);

    setPage("home");
  }


  /* =====================================================
     HOME
     ===================================================== */

  if (page === "home") {
    return (
      <HomePage
        telegramId={telegramId}
        onCreateFilter={
          handleCreateFilter
        }
        onEditFilter={
          handleEditFilter
        }
      />
    );
  }


  /* =====================================================
     CREATE / EDIT
     ===================================================== */

  return (
    <div className="page">

      <button
        type="button"
        className="back-button"
        onClick={handleBack}
      >
        ← Назад
      </button>


      <div className="page-header">

        <div>

          <h1>
            {page === "create"
              ? "Новый фильтр"
              : "Редактирование"}
          </h1>

          <p>
            Настройте параметры поиска
          </p>

        </div>

      </div>


      <FilterForm
        telegramId={telegramId}
        filter={editingFilter}
        onSaved={handleSaved}
        onCancel={handleBack}
      />

    </div>
  );
}


export default App;