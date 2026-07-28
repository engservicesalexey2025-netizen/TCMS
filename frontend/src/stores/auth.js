import { defineStore } from "pinia";
import apiClient from "../api/client";

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("tcms_token") || null,
    user: null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    roleCode: (state) => state.user?.RoleCode || null,
  },
  actions: {
    async login(login, password) {
      const form = new URLSearchParams();
      form.append("username", login);
      form.append("password", password);
      const { data } = await apiClient.post("/auth/login", form, {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      this.token = data.access_token;
      localStorage.setItem("tcms_token", this.token);
      await this.fetchMe();
    },
    async fetchMe() {
      const { data } = await apiClient.get("/auth/me");
      this.user = data;
    },
    logout() {
      this.token = null;
      this.user = null;
      localStorage.removeItem("tcms_token");
    },
  },
});
