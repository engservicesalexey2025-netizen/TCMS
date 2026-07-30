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
    // 403 намеренно НЕ перекидывает на страницу «Недостаточно прав» глобально:
    // доступ к самим страницам уже проверяется в router.beforeEach через
    // auth.can(), а 403 от фонового/второстепенного запроса на разрешённой
    // странице (например, один из нескольких счётчиков на Дашборде, если у
    // роли нет прав на часть из них) не должен выкидывать пользователя со
    // страницы, куда ему разрешено заходить. Компонент, сделавший запрос,
    // сам решает, как обработать отказ.
    return Promise.reject(error);
  },
);

export default apiClient;
