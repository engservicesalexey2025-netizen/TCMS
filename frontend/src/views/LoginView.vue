<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const login = ref("");
const password = ref("");
const remember = ref(true);
const error = ref("");
const loading = ref(false);

const step = ref("credentials"); // 'credentials' | 'mfa'
const mfaToken = ref("");
const mfaCode = ref("");

const auth = useAuthStore();
const router = useRouter();

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    const result = await auth.login(login.value, password.value, remember.value);
    if (result.requiresMfa) {
      mfaToken.value = result.mfaToken;
      step.value = "mfa";
    } else {
      router.push({ name: "dashboard" });
    }
  } catch (e) {
    error.value = e.response?.data?.detail || "Ошибка входа";
  } finally {
    loading.value = false;
  }
}

async function submitMfa() {
  error.value = "";
  loading.value = true;
  try {
    await auth.verifyMfa(mfaToken.value, mfaCode.value, remember.value);
    router.push({ name: "dashboard" });
  } catch (e) {
    error.value = e.response?.data?.detail || "Неверный код подтверждения";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <form v-if="step === 'credentials'" class="login-card" @submit.prevent="submit">
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
      <label class="remember-me">
        <input v-model="remember" type="checkbox" /> Запомнить меня
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="loading">
        {{ loading ? "Входим..." : "Войти" }}
      </button>
      <router-link to="/forgot-password" class="forgot-link">Забыли пароль?</router-link>
      <router-link to="/request-access" class="request-link">
        Нет доступа? Подать заявку
      </router-link>
    </form>

    <form v-else class="login-card" @submit.prevent="submitMfa">
      <h1>Код подтверждения</h1>
      <p class="subtitle">Введите 6-значный код из приложения-аутентификатора</p>
      <label>
        Код
        <input v-model="mfaCode" type="text" inputmode="numeric" maxlength="6" required autofocus />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit" :disabled="loading">
        {{ loading ? "Проверка..." : "Подтвердить" }}
      </button>
      <button type="button" class="link-btn" @click="step = 'credentials'">← Назад</button>
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
.remember-me {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
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
.link-btn {
  background: none;
  color: #2563eb;
  padding: 0;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
  margin: 0;
}
.forgot-link,
.request-link {
  text-align: center;
  font-size: 0.85rem;
  color: #2563eb;
}
</style>
