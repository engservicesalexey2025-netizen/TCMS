<script setup>
import { onMounted, reactive, ref } from "vue";
import apiClient from "../api/client";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const delegations = ref([]);
const form = reactive({ ToUserLogin: "", ExpiresAt: "", Reason: "" });
const error = ref("");
const loading = ref(false);

async function load() {
  const { data } = await apiClient.get("/auth/delegations");
  delegations.value = data;
}

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    const { data: users } = await apiClient.get("/users", { params: { limit: 200 } });
    const target = users.items.find((u) => u.Login === form.ToUserLogin);
    if (!target) {
      error.value = "Пользователь с таким логином не найден";
      return;
    }
    await apiClient.post("/auth/delegations", {
      ToUserId: target.Id,
      ExpiresAt: new Date(form.ExpiresAt).toISOString(),
      Reason: form.Reason || null,
    });
    form.ToUserLogin = "";
    form.ExpiresAt = "";
    form.Reason = "";
    await load();
  } catch (e) {
    error.value = e.response?.data?.detail || "Не удалось делегировать доступ";
  } finally {
    loading.value = false;
  }
}

async function revoke(id) {
  await apiClient.post(`/auth/delegations/${id}/revoke`);
  await load();
}

onMounted(load);
</script>

<template>
  <div class="delegation">
    <p v-if="!auth.can('DELEGATION', 'CREATE')" class="hint">
      Ваша роль не позволяет делегировать полномочия.
    </p>
    <form v-else class="delegation-form" @submit.prevent="submit">
      <label class="field">
        Логин получателя
        <input v-model="form.ToUserLogin" type="text" required />
      </label>
      <label class="field">
        Действует до
        <input v-model="form.ExpiresAt" type="datetime-local" required />
      </label>
      <label class="field">
        Причина
        <input v-model="form.Reason" type="text" />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="primary-btn" type="submit" :disabled="loading">Делегировать</button>
    </form>

    <h3>Активные делегирования</h3>
    <div v-for="d in delegations" :key="d.Id" class="delegation-card">
      <div class="info">
        <strong>{{ d.ToUserLogin }}</strong>
        <span>до {{ new Date(d.ExpiresAt).toLocaleString("ru-RU") }}</span>
        <span v-if="d.Reason">{{ d.Reason }}</span>
      </div>
      <button class="revoke-btn" @click="revoke(d.Id)">Отозвать</button>
    </div>
    <p v-if="delegations.length === 0" class="empty">Нет активных делегирований</p>
  </div>
</template>

<style scoped>
.delegation {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-width: 420px;
}
.hint {
  color: #94a3b8;
  font-size: 0.9rem;
}
.delegation-form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #334155;
}
.field input {
  padding: 0.5rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}
.primary-btn {
  align-self: flex-start;
  padding: 0.5rem 1.2rem;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
}
h3 {
  margin: 0.5rem 0 0;
  font-size: 1rem;
}
.delegation-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.6rem 0.9rem;
}
.info {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  font-size: 0.85rem;
  color: #475569;
}
.revoke-btn {
  border: none;
  background: #fee2e2;
  color: #dc2626;
  padding: 0.35rem 0.7rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
}
.empty {
  color: #94a3b8;
  font-size: 0.85rem;
}
</style>
