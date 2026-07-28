<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const login = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

const auth = useAuthStore();
const router = useRouter();

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    await auth.login(login.value, password.value);
    router.push({ name: "dashboard" });
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка входа";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <form class="login-card" @submit.prevent="submit">
      <h1>TCMS</h1>
      <p class="subtitle">Технический надзор за строительством</p>
      <label>
        Логин
        <input v-model="login" type="text" required autofocus />
      </label>
      <label>
        Пароль
        <input v-model="password" type="password" required />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="loading">
        {{ loading ? "Входим..." : "Войти" }}
      </button>
      <router-link to="/request-access" class="request-link">
        Нет доступа? Подать заявку
      </router-link>
    </form>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
}
.login-card {
  background: #fff;
  padding: 2.5rem;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  width: 340px;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}
h1 {
  margin: 0;
}
.subtitle {
  margin: 0 0 0.5rem;
  color: #64748b;
  font-size: 0.9rem;
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
  font-size: 1rem;
}
button {
  margin-top: 0.5rem;
  padding: 0.6rem;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  font-size: 1rem;
  cursor: pointer;
}
button:disabled {
  opacity: 0.6;
  cursor: default;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
  margin: 0;
}
.request-link {
  text-align: center;
  font-size: 0.85rem;
  color: #2563eb;
}
</style>
