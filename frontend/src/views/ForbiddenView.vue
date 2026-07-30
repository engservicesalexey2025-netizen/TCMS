<script setup>
import { useRouter } from "vue-router";

const router = useRouter();
</script>

<template>
  <div class="forbidden">
    <h1>403</h1>
    <p>Недостаточно прав для доступа к этой странице.</p>
    <button type="button" @click="router.push({ name: 'dashboard' })">На главную</button>
  </div>
</template>

<style scoped>
.forbidden {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  gap: 12px;
}
.forbidden h1 {
  font-size: 48px;
  margin: 0;
  color: #dc2626;
}
.forbidden button {
  margin-top: 8px;
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}
</style>
