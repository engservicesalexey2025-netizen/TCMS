<script setup>
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import apiClient from "../api/client";

const route = useRoute();
const router = useRouter();

const form = reactive({ NewPassword: "", NewPasswordRepeat: "" });
const error = ref("");
const success = ref(false);
const loading = ref(false);

async function submit() {
  error.value = "";
  if (form.NewPassword !== form.NewPasswordRepeat) {
    error.value = "Пароли не совпадают";
    return;
  }
  loading.value = true;
  try {
    await apiClient.post("/auth/reset-password", {
      Token: route.params.token,
      NewPassword: form.NewPassword,
    });
    success.value = true;
    setTimeout(() => router.push({ name: "login" }), 2000);
  } catch (e) {
    error.value = e.response?.data?.detail || "Ссылка недействительна или устарела";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>Новый пароль</h1>
      <p class="subtitle">Ссылка действительна 15 минут с момента выдачи.</p>
      <template v-if="!success">
        <form @submit.prevent="submit">
          <label>
            Новый пароль
            <input v-model="form.NewPassword" type="password" required minlength="8" autofocus />
          </label>
          <label>
            Повторите пароль
            <input v-model="form.NewPasswordRepeat" type="password" required />
          </label>
          <p v-if="error" class="error">{{ error }}</p>
          <button type="submit" :disabled="loading">{{ loading ? "Сохранение..." : "Сохранить" }}</button>
        </form>
        <router-link to="/forgot-password" class="back-link">Запросить новую ссылку</router-link>
      </template>
      <p v-else class="success">Пароль изменён, сейчас вы будете перенаправлены на вход.</p>
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
  font-size: 0.85rem;
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
.success {
  color: #16a34a;
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
