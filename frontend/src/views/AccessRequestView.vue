<script setup>
import { onMounted, reactive, ref } from "vue";
import apiClient from "../api/client";

const form = reactive({
  FullName: "",
  Email: "",
  Phone: "",
  Organization: "",
  Position: "",
  RequestedRoleId: "",
  RequestedOrgUnitId: "",
  RequestedProjectId: "",
  Comment: "",
});
const roles = ref([]);
const orgUnits = ref([]);
const projects = ref([]);
const submitted = ref(false);
const error = ref("");

onMounted(async () => {
  const [rolesRes, orgUnitsRes, projectsRes] = await Promise.all([
    apiClient.get("/public/roles"),
    apiClient.get("/public/org-units"),
    apiClient.get("/public/projects"),
  ]);
  roles.value = rolesRes.data;
  orgUnits.value = orgUnitsRes.data;
  projects.value = projectsRes.data;
});

async function submit() {
  error.value = "";
  try {
    await apiClient.post("/access-requests", {
      FullName: form.FullName,
      Email: form.Email,
      Phone: form.Phone || null,
      Organization: form.Organization || null,
      Position: form.Position || null,
      RequestedRoleId: form.RequestedRoleId,
      RequestedOrgUnitId: form.RequestedOrgUnitId || null,
      RequestedProjectId: form.RequestedProjectId || null,
      Comment: form.Comment || null,
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
        <input v-model="form.FullName" type="text" required />
      </label>
      <label>
        Email
        <input v-model="form.Email" type="email" required />
      </label>
      <label>
        Телефон
        <input v-model="form.Phone" type="text" />
      </label>
      <label>
        Организация
        <input v-model="form.Organization" type="text" />
      </label>
      <label>
        Должность
        <input v-model="form.Position" type="text" />
      </label>
      <label>
        Запрашиваемая роль
        <select v-model="form.RequestedRoleId" required>
          <option value="" disabled>Выберите роль</option>
          <option v-for="r in roles" :key="r.Id" :value="r.Id">{{ r.Name }}</option>
        </select>
      </label>
      <label>
        Подразделение
        <select v-model="form.RequestedOrgUnitId">
          <option value="">— не требуется —</option>
          <option v-for="u in orgUnits" :key="u.Id" :value="u.Id">{{ u.Name }}</option>
        </select>
      </label>
      <label>
        Проект
        <select v-model="form.RequestedProjectId">
          <option value="">— не требуется —</option>
          <option v-for="p in projects" :key="p.Id" :value="p.Id">{{ p.Name }}</option>
        </select>
      </label>
      <label>
        Причина получения доступа / комментарий
        <textarea v-model="form.Comment" rows="3"></textarea>
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
  padding: 2rem 0;
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
select,
textarea {
  padding: 0.55rem 0.7rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 1rem;
  font-family: inherit;
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
