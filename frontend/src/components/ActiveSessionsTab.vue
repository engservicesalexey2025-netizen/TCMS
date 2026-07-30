<script setup>
import { onMounted, ref } from "vue";
import apiClient from "../api/client";

const sessions = ref([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    const { data } = await apiClient.get("/auth/sessions");
    sessions.value = data;
  } finally {
    loading.value = false;
  }
}

async function revoke(id) {
  if (!window.confirm("Завершить эту сессию?")) return;
  await apiClient.post(`/auth/sessions/${id}/revoke`);
  await load();
}

function fmt(dt) {
  return new Date(dt).toLocaleString("ru-RU");
}

onMounted(load);
</script>

<template>
  <div class="sessions">
    <div v-for="s in sessions" :key="s.Id" class="session-card">
      <div class="info">
        <strong>{{ s.UserAgent || "Неизвестное устройство" }}</strong>
        <span>IP: {{ s.IpAddress || "—" }}</span>
        <span>Вход: {{ fmt(s.IssuedAt) }}</span>
        <span v-if="s.IsCurrent" class="current-badge">Текущая сессия</span>
      </div>
      <button v-if="!s.IsCurrent" class="revoke-btn" @click="revoke(s.Id)">Завершить</button>
    </div>
    <p v-if="!loading && sessions.length === 0" class="empty">Активных сессий нет</p>
  </div>
</template>

<style scoped>
.sessions {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.session-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem 1rem;
}
.info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  font-size: 0.85rem;
  color: #475569;
}
.current-badge {
  color: #16a34a;
  font-weight: 600;
}
.revoke-btn {
  border: none;
  background: #fee2e2;
  color: #dc2626;
  padding: 0.4rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
}
.empty {
  color: #94a3b8;
  text-align: center;
  padding: 1rem;
}
</style>
