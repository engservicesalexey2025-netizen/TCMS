<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import apiClient from "../../api/client";

const route = useRoute();
const router = useRouter();
const requestId = route.params.id;

const request = ref(null);
const roles = ref([]);
const orgUnits = ref([]);
const projects = ref([]);
const selectedRoleIds = ref([]);
const overrideLogin = ref("");
const overridePassword = ref("");
const result = ref(null);
const error = ref("");

function lookupName(list, id) {
  return list.find((x) => x.Id === id)?.Name ?? "—";
}

async function load() {
  const [reqRes, rolesRes, orgUnitsRes, projectsRes] = await Promise.all([
    apiClient.get(`/access-requests/${requestId}`),
    apiClient.get("/public/roles"),
    apiClient.get("/public/org-units"),
    apiClient.get("/public/projects"),
  ]);
  request.value = reqRes.data;
  roles.value = rolesRes.data;
  orgUnits.value = orgUnitsRes.data;
  projects.value = projectsRes.data;
  selectedRoleIds.value = [request.value.RequestedRoleId];
}

function toggleRole(id) {
  const i = selectedRoleIds.value.indexOf(id);
  if (i >= 0) selectedRoleIds.value.splice(i, 1);
  else selectedRoleIds.value.push(id);
}

async function approve() {
  error.value = "";
  try {
    const { data } = await apiClient.post(`/access-requests/${requestId}/decide`, {
      Approve: true,
      RoleIds: selectedRoleIds.value,
      Login: overrideLogin.value || null,
      TemporaryPassword: overridePassword.value || null,
    });
    result.value = data.Comment;
  } catch (e) {
    error.value = e.response?.data?.detail || "Не удалось одобрить заявку";
  }
}

async function reject() {
  await apiClient.post(`/access-requests/${requestId}/decide`, { Approve: false });
  router.push({ name: "access-requests-admin" });
}

onMounted(load);
</script>

<template>
  <div v-if="request" class="page">
    <button class="back-btn" @click="router.push({ name: 'access-requests-admin' })">← К списку заявок</button>
    <h2>Заявка: {{ request.FullName }}</h2>

    <div v-if="result" class="result-banner">{{ result }}</div>

    <template v-else>
      <section class="card">
        <h3>Проверка</h3>
        <dl class="grid-dl">
          <dt>ФИО</dt><dd>{{ request.FullName }}</dd>
          <dt>Email</dt><dd>{{ request.Email }}</dd>
          <dt>Телефон</dt><dd>{{ request.Phone || "—" }}</dd>
          <dt>Организация</dt><dd>{{ request.Organization || "—" }}</dd>
          <dt>Должность</dt><dd>{{ request.Position || "—" }}</dd>
          <dt>Запрошенное подразделение</dt><dd>{{ request.RequestedOrgUnitId ? lookupName(orgUnits, request.RequestedOrgUnitId) : "—" }}</dd>
          <dt>Запрошенный проект</dt><dd>{{ request.RequestedProjectId ? lookupName(projects, request.RequestedProjectId) : "—" }}</dd>
          <dt>Комментарий</dt><dd>{{ request.Comment || "—" }}</dd>
        </dl>
      </section>

      <section class="card">
        <h3>Назначить роль(-и)</h3>
        <div class="role-list">
          <label v-for="r in roles" :key="r.Id" class="role-item">
            <input type="checkbox" :checked="selectedRoleIds.includes(r.Id)" @change="toggleRole(r.Id)" />
            {{ r.Name }}
          </label>
        </div>
      </section>

      <section class="card">
        <h3>Учётные данные (необязательно)</h3>
        <label class="field">
          Логин (если не указать — сгенерируется из email)
          <input v-model="overrideLogin" type="text" />
        </label>
        <label class="field">
          Временный пароль (если не указать — сгенерируется автоматически)
          <input v-model="overridePassword" type="text" />
        </label>
      </section>

      <p v-if="error" class="error">{{ error }}</p>
      <div class="actions">
        <button class="reject-btn" @click="reject">Отклонить</button>
        <button class="approve-btn" @click="approve">Сохранить и создать пользователя</button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.back-btn {
  border: none;
  background: none;
  color: #2563eb;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0;
  margin-bottom: 0.5rem;
}
h2 {
  margin: 0 0 1rem;
}
.card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.25rem;
  margin-bottom: 1rem;
}
.card h3 {
  margin: 0 0 0.75rem;
}
.grid-dl {
  display: grid;
  grid-template-columns: 220px 1fr;
  row-gap: 0.6rem;
  margin: 0;
}
.grid-dl dt {
  color: #64748b;
  font-size: 0.85rem;
}
.grid-dl dd {
  margin: 0;
  font-size: 0.9rem;
}
.role-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.role-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #334155;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #334155;
  margin-bottom: 0.75rem;
}
.field input {
  padding: 0.45rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
}
.actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
}
.approve-btn,
.reject-btn {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}
.approve-btn {
  background: #2563eb;
  color: #fff;
}
.reject-btn {
  background: #fee2e2;
  color: #dc2626;
}
.result-banner {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 1rem;
  border-radius: 8px;
}
</style>
