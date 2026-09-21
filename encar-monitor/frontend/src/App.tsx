import { useEffect, useState } from "react";

import HomePage from "./pages/HomePage";
import FilterForm from "./components/FilterForm";
import { getCurrentUser } from "./api/client";

import type { Filter } from "./types/filter";

type Page = "home" | "create" | "edit";

function App() {
  const [page, setPage] = useState<Page>("home");
  const [editingFilter, setEditingFilter] = useState<Filter | null>(null);
  const [authorized, setAuthorized] = useState<boolean | null>(null);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    void getCurrentUser()
      .then(() => setAuthorized(true))
      .catch((error) => {
        console.error(error);
        setAuthError(
          error instanceof Error
            ? error.message
            : "Не удалось подтвердить Telegram",
        );
        setAuthorized(false);
      });
  }, []);

  function handleCreateFilter() {
    setEditingFilter(null);
    setPage("create");
  }

  function handleEditFilter(filter: Filter) {
    setEditingFilter(filter);
    setPage("edit");
  }

  function handleBack() {
    setEditingFilter(null);
    setPage("home");
  }

  function handleSaved() {
    setEditingFilter(null);
    setPage("home");
  }

  if (authorized === null) {
    return (
      <div className="page auth-state">
        <div className="auth-card">
          <strong>Проверяем Telegram...</strong>
          <span>Подтверждаем доступ к Encar Монитору</span>
        </div>
      </div>
    );
  }

  if (!authorized) {
    return (
      <div className="page auth-state">
        <div className="auth-card">
          <strong>⛔ Доступ не подтверждён</strong>
          <span>{authError}</span>
          <small>
            Откройте приложение из Telegram или проверьте настройки Mini App.
          </small>
        </div>
      </div>
    );
  }

  if (page === "home") {
    return (
      <HomePage
        onCreateFilter={handleCreateFilter}
        onEditFilter={handleEditFilter}
      />
    );
  }

  return (
    <div className="page">
      <button type="button" className="back-button" onClick={handleBack}>
        ← Назад
      </button>

      <div className="page-header">
        <div>
          <h1>{page === "create" ? "Новый фильтр" : "Редактирование"}</h1>
          <p>Настройте параметры поиска</p>
        </div>
      </div>

      <FilterForm
        filter={editingFilter}
        onSaved={handleSaved}
        onCancel={handleBack}
      />
    </div>
  );
}

export default App;
