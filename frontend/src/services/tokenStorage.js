/**
 * Абстракция над хранилищем токена: "Запомнить меня" переключает backing
 * store между localStorage (переживает закрытие вкладки) и sessionStorage
 * (стирается вместе с вкладкой) — иначе чекбокс на экране входа был бы
 * чисто декоративным.
 */
const TOKEN_KEY = "tcms_token";
const REMEMBER_KEY = "tcms_remember";

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY) || null;
}

export function setToken(token, remember) {
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
  if (remember) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(REMEMBER_KEY, "1");
  } else {
    sessionStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(REMEMBER_KEY, "0");
  }
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REMEMBER_KEY);
}
