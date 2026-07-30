import axios from "axios";
import { getToken } from "../services/tokenStorage";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
});

apiClient.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Ленивый импорт — auth.js импортирует этот файл, прямой импорт наверху
      // создал бы цикл; на момент вызова обработчика оба модуля уже загружены.
      const { useAuthStore } = await import("../stores/auth");
      useAuthStore().logout();
    }
    if (error.response?.status === 403) {
      const { default: router } = await import("../router");
      router.push({ name: "forbidden" });
    }
    return Promise.reject(error);
  },
);

export default apiClient;
