<script setup>
import { reactive, ref } from "vue";
import apiClient from "../api/client";

const emit = defineEmits(["done"]);

const form = reactive({ CurrentPassword: "", NewPassword: "", NewPasswordRepeat: "" });
const error = ref("");
const success = ref(false);
const saving = ref(false);

async function submit() {
  error.value = "";
  success.value = false;
  if (form.NewPassword !== form.NewPasswordRepeat) {
    error.value = "Новый пароль и повтор не совпадают";
    return;
  }
  saving.value = true;
  try {
    await apiClient.post("/auth/change-password", {
      CurrentPassword: form.CurrentPassword,
      NewPassword: form.NewPassword,
    });
    success.value = true;
    form.CurrentPassword = "";
    form.NewPassword = "";
    form.NewPasswordRepeat = "";
    emit("done");
  } catch (e) {
    error.value = e.response?.data?.detail || "Не удалось изменить пароль";
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <form class="change-password-form" @submit.prevent="submit">
    <label class="field">
      Текущий пароль
      <input v-model="form.CurrentPassword" type="password" required autocomplete="current-password" />
    </label>
    <label class="field">
      Новый пароль
      <input v-model="form.NewPassword" type="password" required autocomplete="new-password" minlength="8" />
    </label>
    <label class="field">
      Повторите новый пароль
      <input v-model="form.NewPasswordRepeat" type="password" required autocomplete="new-password" />
    </label>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="success" class="success">Пароль изменён.</p>
    <button class="primary-btn" type="submit" :disabled="saving">
      {{ saving ? "Сохранение..." : "Изменить пароль" }}
    </button>
  </form>
</template>

<style scoped>
.change-password-form {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  max-width: 360px;
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
.error {
  color: #dc2626;
  font-size: 0.85rem;
}
.success {
  color: #16a34a;
  font-size: 0.85rem;
}
.primary-btn {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
  align-self: flex-start;
}
.primary-btn:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
