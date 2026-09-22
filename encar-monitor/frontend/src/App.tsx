import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import HomePage from "./pages/HomePage";
import FilterForm from "./components/FilterForm";
import { getCurrentUser, login, logout, register } from "./api/client";

import type { Filter } from "./types/filter";

type Page = "home" | "create" | "edit";

function AuthPage({ onAuthorized }: { onAuthorized: () => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [masterPassword, setMasterPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);

    try {
      if (mode === "login") {
        await login(username, password);
      } else {
        await register(username, password, masterPassword);
      }
      onAuthorized();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Ошибка авторизации");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page auth-state">
      <form className="auth-card auth-form" onSubmit={submit}>
        <h1>Encar Monitor</h1>
        <p>{mode === "login" ? "Войдите в аккаунт" : "Создайте аккаунт"}</p>

        <input
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          placeholder="Логин"
          autoComplete="username"
          minLength={3}
          maxLength={50}
          required
        />

        <input
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          placeholder="Пароль (минимум 8 символов)"
          type="password"
          autoComplete={mode === "login" ? "current-password" : "new-password"}
          minLength={8}
          maxLength={128}
          required
        />

        {mode === "register" && (
          <input
            value={masterPassword}
            onChange={(event) => setMasterPassword(event.target.value)}
            placeholder="Мастер-пароль"
            type="password"
            autoComplete="off"
            maxLength={128}
            required
          />
        )}

        {error && <span className="auth-error">{error}</span>}

        <button type="submit" disabled={busy}>
          {busy
            ? "Подождите..."
            : mode === "login"
              ? "Войти"
              : "Зарегистрироваться"}
        </button>

        <button
          type="button"
          className="auth-switch"
          onClick={() => {
            setMode(mode === "login" ? "register" : "login");
            setError("");
          }}
        >
          {mode === "login" ? "Создать аккаунт" : "У меня уже есть аккаунт"}
        </button>
      </form>
    </div>
  );
}

function App() {
  const [page, setPage] = useState<Page>("home");
  const [editingFilter, setEditingFilter] = useState<Filter | null>(null);
  const [authorized, setAuthorized] = useState<boolean | null>(null);

  useEffect(() => {
    void getCurrentUser()
      .then(() => setAuthorized(true))
      .catch(() => setAuthorized(false));
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

  function handleLogout() {
    logout();
    setAuthorized(false);
    setPage("home");
  }

  if (authorized === null) {
    return (
      <div className="page auth-state">
        <div className="auth-card">
          <strong>Проверяем авторизацию...</strong>
          <span>Подготавливаем Encar Monitor</span>
        </div>
      </div>
    );
  }

  if (!authorized) {
    return <AuthPage onAuthorized={() => setAuthorized(true)} />;
  }

  if (page === "home") {
    return (
      <>
        <HomePage
          onCreateFilter={handleCreateFilter}
          onEditFilter={handleEditFilter}
        />
        <button type="button" className="logout-button" onClick={handleLogout}>
          Выйти
        </button>
      </>
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
