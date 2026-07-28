<script setup>
import { onMounted, ref } from "vue";
import apiClient from "../api/client";

const fullName = ref("");
const email = ref("");
const roleId = ref("");
const orgUnitId = ref("");
const roles = ref([]);
const orgUnits = ref([]);
const submitted = ref(false);
const error = ref("");

onMounted(async () => {
  const [rolesRes, orgUnitsRes] = await Promise.all([
    apiClient.get("/public/roles"),
    apiClient.get("/public/org-units"),
  ]);
  roles.value = rolesRes.data;
  orgUnits.value = orgUnitsRes.data;
});

async function submit() {
  error.value = "";
  try {
    await apiClient.post("/access-requests", {
      FullName: fullName.value,
      Email: email.value,
      RequestedRoleId: roleId.value,
      RequestedOrgUnitId: orgUnitId.value || null,
    });
    submitted.value = true;
  } catch (e) {
    error.value = e.response?.data?.detail || "Не удалось отправить заявку";
  }
}
</script>

<template>
  <div class="page">
    <form v-if="!submitted" class="card" @submit.prevent="submit">
      <h1>Заявка на доступ к TCMS</h1>
      <label>
        ФИО
        <input v-model="fullName" type="text" required />
      </label>
      <label>
        Email
        <input v-model="email" type="email" required />
      </label>
      <label>
        Запрашиваемая роль
        <select v-model="roleId" required>
          <option value="" disabled>Выберите роль</option>
          <option v-for="r in roles" :key="r.Id" :value="r.Id">{{ r.Name }}</option>
        </select>
      </label>
      <label>
        Организационная единица
        <select v-model="orgUnitId">
          <option value="">— не требуется —</option>
          <option v-for="u in orgUnits" :key="u.Id" :value="u.Id">{{ u.Name }}</option>
        </select>
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button type="submit">Отправить заявку</button>
      <router-link to="/login" class="back-link">Назад ко входу</router-link>
    </form>
    <div v-else class="card">
      <h1>Заявка отправлена</h1>
      <p>Администратор рассмотрит заявку и создаст учётную запись.</p>
      <router-link to="/login" class="back-link">Назад ко входу</router-link>
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
  width: 380px;
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
input,
select {
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
.error {
  color: #dc2626;
  font-size: 0.85rem;
  margin: 0;
}
.back-link {
  text-align: center;
  font-size: 0.85rem;
  color: #2563eb;
}
</style>
