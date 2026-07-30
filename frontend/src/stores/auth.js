import { defineStore } from "pinia";
import apiClient from "../api/client";
import { clearToken, getToken, setToken } from "../services/tokenStorage";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: getToken(),
    user: null,
    fetchingMe: null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    roles: (state) => state.user?.Roles ?? [],
    roleCodes: (state) => (state.user?.Roles ?? []).map((r) => r.Code),
    mustChangePassword: (state) => !!state.user?.MustChangePassword,
    is2FAEnabled: (state) => !!state.user?.Is2FAEnabled,
    isViewingAs: (state) => !!state.user?.ViewAs,
    viewAsBanner: (state) => state.user?.ViewAs ?? null,
    permissions: (state) => state.user?.Permissions ?? {},
    // Единая точка проверки прав по всему приложению — вместо булевых
    // isAdmin/isEngineer, потому что роли/права теперь настраиваются
    // администратором в рантайме, а не фиксированы в коде.
    can: (state) => (module, action) => {
      const entry = state.user?.Permissions?.[module];
      return !!entry?.actions?.includes(action);
    },
    // `Permissions[module].columns` на бэкенде — список СКРЫТЫХ полей
    // (не белый список видимых): так бэкенду не нужен канонический список
    // полей сущности, только исключения.
    canSeeColumn: (state) => (module, field) => {
      const entry = state.user?.Permissions?.[module];
      if (!entry) return true;
      return !entry.columns?.includes(field);
    },
    hasAnyModuleAccess: (state) => Object.keys(state.user?.Permissions ?? {}).length > 0,
  },
  actions: {
    async login(login, password, remember = true) {
      const form = new URLSearchParams();
      form.append("username", login);
      form.append("password", password);
      const { data } = await apiClient.post("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      if (data.requires_mfa) {
        return { requiresMfa: true, mfaToken: data.access_token };
      }
      this._applyToken(data.access_token, remember);
      await this.fetchMe();
      return { requiresMfa: false };
    },
    async verifyMfa(mfaToken, code, remember = true) {
      const { data } = await apiClient.post("/auth/login/verify-mfa", {
        MfaToken: mfaToken,
        Code: code,
      });
      this._applyToken(data.access_token, remember);
      await this.fetchMe();
    },
    _applyToken(token, remember) {
      this.token = token;
      setToken(token, remember);
    },
    async fetchMe() {
      if (this.fetchingMe) return this.fetchingMe;
      this.fetchingMe = apiClient
        .get("/auth/me")
        .then(({ data }) => {
          this.user = data;
        })
        .finally(() => {
          this.fetchingMe = null;
        });
      return this.fetchingMe;
    },
    async logout({ redirect = true } = {}) {
      try {
        if (this.token) await apiClient.post("/auth/logout");
      } catch {
        // logout - best effort: сессия отзывается на сервере, но если сеть
        // недоступна, всё равно чистим локальное состояние ниже.
      }
      this.token = null;
      this.user = null;
      clearToken();
      if (redirect) {
        const { default: router } = await import("../router");
        if (router.currentRoute.value.name !== "login") {
          router.push({ name: "login" });
        }
      }
    },
  },
});
