<script setup>
import { computed, onMounted, ref } from "vue";
import apiClient from "../api/client";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const sessions = ref([]);
const total = ref(0);
const skip = ref(0);
const limit = ref(20);
const cleaning = ref(false);
const canCleanup = computed(() => auth.can("ROLES", "MANAGE"));

// Право на удаление конкретной сессии совпадает с правом на импорт этой
// сущности (тот же профиль, что бэкенд проверяет в _require_write_access).
function canDelete(entityType) {
  return auth.can(entityType.toUpperCase(), "IMPORT");
}

const STATUS_LABELS = {
  UPLOADED: "Загружен",
  VALIDATED: "Проверен",
  REVIEW: "На ревью",
  APPLYING: "Применяется",
  APPLIED: "Применён",
  PARTIALLY_APPLIED: "Частично применён",
  FAILED: "Ошибка",
  CANCELLED: "Отменён",
};

async function load() {
  const { data } = await apiClient.get("/imports/sessions", {
    params: { skip: skip.value, limit: limit.value },
  });
  sessions.value = data.items;
  total.value = data.total;
}

async function deleteSession(session) {
  if (!window.confirm(`Удалить запись импорта «${session.FileName}» из истории?`)) return;
  await apiClient.delete(`/imports/sessions/${session.Id}`);
  await load();
}

async function cleanupOld() {
  if (!window.confirm("Удалить все записи истории импортов старше 60 дней?")) return;
  cleaning.value = true;
  try {
    const { data } = await apiClient.post("/imports/sessions/cleanup", null, {
      params: { older_than_days: 60 },
    });
    window.alert(`Удалено записей: ${data.deleted}`);
    skip.value = 0;
    await load();
  } finally {
    cleaning.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div>
    <div class="header">
      <h2>История импортов</h2>
      <button v-if="canCleanup" class="secondary-btn" :disabled="cleaning" @click="cleanupOld">
        {{ cleaning ? "Очистка..." : "Очистить старше 60 дней" }}
      </button>
    </div>
    <table class="grid">
      <thead>
        <tr>
          <th>Дата</th>
          <th>Сущность</th>
          <th>Файл</th>
          <th>Статус</th>
          <th>Совпало</th>
          <th>Новое</th>
          <th>Расхождение</th>
          <th>Ошибки</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="s in sessions" :key="s.Id">
          <td>{{ new Date(s.CreatedDate).toLocaleString("ru-RU") }}</td>
          <td>{{ s.EntityType }}</td>
          <td>{{ s.FileName }}</td>
          <td>{{ STATUS_LABELS[s.Status] || s.Status }}</td>
          <td>{{ s.Counts?.IDENTICAL || 0 }}</td>
          <td>{{ s.Counts?.NEW || 0 }}</td>
          <td>{{ s.Counts?.CONFLICT || 0 }}</td>
          <td>{{ s.Counts?.ERROR || 0 }}</td>
          <td>
            <button v-if="canDelete(s.EntityType)" class="link-btn danger" @click="deleteSession(s)">
              Удалить
            </button>
          </td>
        </tr>
        <tr v-if="sessions.length === 0">
          <td colspan="9" class="empty">Импортов ещё не было</td>
        </tr>
      </tbody>
    </table>
    <div class="pager">
      <button :disabled="skip === 0" @click="skip = Math.max(0, skip - limit); load()">← Назад</button>
      <span>{{ skip + 1 }}–{{ Math.min(skip + limit, total) }} из {{ total }}</span>
      <button :disabled="skip + limit >= total" @click="skip += limit; load()">Вперёд →</button>
    </div>
  </div>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.header h2 {
  margin: 0;
}
.secondary-btn {
  padding: 0.4rem 0.9rem;
  border: 1px solid #2563eb;
  border-radius: 6px;
  background: #fff;
  color: #2563eb;
  cursor: pointer;
  font-size: 0.85rem;
}
.link-btn {
  border: none;
  background: none;
  color: #2563eb;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0;
}
.link-btn.danger {
  color: #dc2626;
}
.grid {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}
.grid th,
.grid td {
  text-align: left;
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.9rem;
}
.empty {
  text-align: center;
  color: #94a3b8;
  padding: 1.5rem;
}
.pager {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.75rem;
  font-size: 0.85rem;
  color: #475569;
}
</style>
