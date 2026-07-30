<script setup>
import { ref } from "vue";
import apiClient from "../api/client";

const email = ref("");
const detail = ref("");
const error = ref("");
const submitted = ref(false);
const loading = ref(false);

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    const { data } = await apiClient.post("/auth/forgot-password", { Email: email.value });
    detail.value = data.Detail;
    submitted.value = true;
  } catch (e) {
    error.value = e.response?.data?.detail || "Не удалось отправить запрос";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>Забыли пароль?</h1>
      <template v-if="!submitted">
        <p class="subtitle">Укажите email, привязанный к учётной записи.</p>
        <form @submit.prevent="submit">
          <label>
            Email
            <input v-model="email" type="email" required autofocus />
          </label>
          <p v-if="error" class="error">{{ error }}</p>
          <button type="submit" :disabled="loading">{{ loading ? "Отправка..." : "Отправить" }}</button>
        </form>
      </template>
      <p v-else class="detail">{{ detail }}</p>
      <router-link to="/login" class="back-link">← Вернуться ко входу</router-link>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
}
.card {
  background: #fff;
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  width: 360px;
}
h1 {
  margin: 0 0 0.5rem;
  font-size: 1.3rem;
}
.subtitle {
  color: #64748b;
  font-size: 0.9rem;
  margin: 0 0 1rem;
}
form {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.9rem;
  color: #334155;
}
input {
  padding: 0.55rem 0.7rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}
button {
  padding: 0.6rem;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
  margin: 0;
}
.detail {
  color: #334155;
  font-size: 0.9rem;
}
.back-link {
  display: block;
  margin-top: 1rem;
  text-align: center;
  font-size: 0.85rem;
  color: #2563eb;
}
</style>
