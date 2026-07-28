<script setup>
import { onMounted, ref } from "vue";
import apiClient from "../api/client";

const sessions = ref([]);
const total = ref(0);
const skip = ref(0);
const limit = ref(20);

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

onMounted(load);
</script>

<template>
  <div>
    <h2>История импортов</h2>
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
        </tr>
        <tr v-if="sessions.length === 0">
          <td colspan="8" class="empty">Импортов ещё не было</td>
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
