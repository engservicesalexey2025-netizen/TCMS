// Единый формат дат по всему приложению — день.месяц.год (см. фидбэк
// клиента: "везде где есть поля выбора даты ... дата отображалась
// день.месяц.год"). Хранение/API остаются в ISO (YYYY-MM-DD) — эти
// функции только конвертируют между ISO и отображаемым видом.

export function isoToDisplayDate(iso) {
  if (!iso) return "";
  const [y, m, d] = String(iso).split("T")[0].split("-");
  if (!y || !m || !d) return "";
  return `${d}.${m}.${y}`;
}

export function displayDateToIso(display) {
  const match = String(display || "").match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
  if (!match) return undefined;
  const [, d, m, y] = match;
  return `${y}-${m}-${d}`;
}
