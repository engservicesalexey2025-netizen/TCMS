<script setup>
import { useRouter } from "vue-router";
import ChangePasswordForm from "../components/ChangePasswordForm.vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const router = useRouter();

async function onDone() {
  await auth.fetchMe();
  router.push({ name: "dashboard" });
}
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>Смена пароля</h1>
      <p v-if="auth.mustChangePassword" class="notice">
        Вам выдан временный пароль — прежде чем продолжить работу, установите собственный.
      </p>
      <ChangePasswordForm @done="onDone" />
    </div>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #f1f5f9;
}
.card {
  background: #fff;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 420px;
}
.card h1 {
  margin: 0 0 1rem;
  font-size: 1.3rem;
}
.notice {
  background: #fef3c7;
  color: #92400e;
  padding: 0.6rem 0.8rem;
  border-radius: 6px;
  font-size: 0.85rem;
  margin-bottom: 1rem;
}
</style>
