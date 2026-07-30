<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import apiClient from "../../api/client";

const route = useRoute();
const router = useRouter();
const userId = route.params.id;

const detail = ref(null);
const allRoles = ref([]);
const allOrgUnits = ref([]);
const allProjects = ref([]);
const message = ref("");

// Роли: Map<RoleId, ExpiresAt|null>, чекбокс определяется присутствием ключа.
const roleSelection = reactive({});

async function load() {
  const [detailRes, rolesRes, orgUnitsRes, projectsRes] = await Promise.all([
    apiClient.get(`/users/${userId}`),
    apiClient.get("/roles", { params: { limit: 100 } }),
    apiClient.get("/org-units", { params: { limit: 200 } }),
    apiClient.get("/public/projects"),
  ]);
  detail.value = detailRes.data;
  allRoles.value = rolesRes.data.items;
  allOrgUnits.value = orgUnitsRes.data.items;
  allProjects.value = projectsRes.data;

  Object.keys(roleSelection).forEach((k) => delete roleSelection[k]);
  for (const r of detail.value.Roles) {
    roleSelection[r.RoleId] = r.ExpiresAt;
  }
}

function toggleRole(roleId) {
  if (roleId in roleSelection) {
    delete roleSelection[roleId];
  } else {
    roleSelection[roleId] = null;
  }
}

async function saveRoles() {
  const payload = Object.entries(roleSelection).map(([RoleId, ExpiresAt]) => ({ RoleId, ExpiresAt }));
  const { data } = await apiClient.put(`/users/${userId}/roles`, payload);
  detail.value = data;
  message.value = "Роли сохранены";
}

// Org access
const orgSelection = reactive({});
function initOrgSelection() {
  Object.keys(orgSelection).forEach((k) => delete orgSelection[k]);
  for (const a of detail.value.OrgAccess) orgSelection[a.OrgUnitId] = a.ExpiresAt;
}
function toggleOrg(orgUnitId) {
  if (orgUnitId in orgSelection) {
    delete orgSelection[orgUnitId];
  } else {
    orgSelection[orgUnitId] = null;
  }
}
async function saveOrgAccess() {
  const payload = Object.entries(orgSelection).map(([OrgUnitId, ExpiresAt]) => ({ OrgUnitId, ExpiresAt }));
  const { data } = await apiClient.put(`/users/${userId}/org-access`, payload);
  detail.value = data;
  message.value = "Доступ по организациям сохранён";
}

// Доступ по проектам (DataScopes, ScopeType=PROJECT) — ручное исключение
// сверх Assignments (§15 ТЗ), например наблюдателю/подрядчику без назначения
// на проект.
const projectSelection = reactive({});
function initProjectSelection() {
  Object.keys(projectSelection).forEach((k) => delete projectSelection[k]);
  for (const s of detail.value.DataScopes) {
    if (s.ScopeType === "PROJECT") projectSelection[s.ScopeId] = s.ExpiresAt;
  }
}
function toggleProject(projectId) {
  if (projectId in projectSelection) {
    delete projectSelection[projectId];
  } else {
    projectSelection[projectId] = null;
  }
}
async function saveProjectAccess() {
  // PUT заменяет ВСЕ DataScopes пользователя разом — сохраняем нетронутыми
  // записи других ScopeType (сегодня их не создаёт никакой другой экран,
  // но эндпойнт не различает типы при замене).
  const otherScopes = detail.value.DataScopes.filter((s) => s.ScopeType !== "PROJECT");
  const payload = [
    ...otherScopes.map((s) => ({
      ScopeType: s.ScopeType, ScopeId: s.ScopeId, ExpiresAt: s.ExpiresAt, Reason: s.Reason,
    })),
    ...Object.entries(projectSelection).map(([ScopeId, ExpiresAt]) => ({
      ScopeType: "PROJECT",
      ScopeId,
      ExpiresAt,
    })),
  ];
  const { data } = await apiClient.put(`/users/${userId}/data-scopes`, payload);
  detail.value = data;
  initProjectSelection();
  message.value = "Доступ по проектам сохранён";
}

// Permission overrides
const overrideForm = reactive({ Module: "", Action: "VIEW", Effect: "GRANT", Reason: "" });
async function addOverride() {
  const payload = detail.value.PermissionOverrides.map((o) => ({
    Module: o.Module, Action: o.Action, Effect: o.Effect, ExpiresAt: o.ExpiresAt, Reason: o.Reason,
  }));
  payload.push({ Module: overrideForm.Module, Action: overrideForm.Action, Effect: overrideForm.Effect, Reason: overrideForm.Reason || null });
  const { data } = await apiClient.put(`/users/${userId}/permissions`, payload);
  detail.value = data;
  overrideForm.Module = "";
  overrideForm.Reason = "";
}
async function removeOverride(module, action) {
  const payload = detail.value.PermissionOverrides
    .filter((o) => !(o.Module === module && o.Action === action))
    .map((o) => ({ Module: o.Module, Action: o.Action, Effect: o.Effect, ExpiresAt: o.ExpiresAt, Reason: o.Reason }));
  const { data } = await apiClient.put(`/users/${userId}/permissions`, payload);
  detail.value = data;
}

onMounted(async () => {
  await load();
  initOrgSelection();
  initProjectSelection();
});
</script>

<template>
  <div v-if="detail" class="page">
    <button class="back-btn" @click="router.push({ name: 'admin-roles' })">← Назад</button>
    <h2>{{ detail.Login }} <span class="email">({{ detail.Email }})</span></h2>

    <section class="card">
      <h3>Роли</h3>
      <div class="role-list">
        <label v-for="r in allRoles" :key="r.Id" class="role-item">
          <input type="checkbox" :checked="r.Id in roleSelection" @change="toggleRole(r.Id)" />
          {{ r.Name }}
          <input
            v-if="r.Id in roleSelection"
            v-model="roleSelection[r.Id]"
            type="datetime-local"
            class="expiry-input"
            placeholder="Бессрочно"
          />
        </label>
      </div>
      <button class="primary-btn" @click="saveRoles">Сохранить роли</button>
    </section>

    <section class="card">
      <h3>Доступ по организациям</h3>
      <div class="role-list">
        <label v-for="o in allOrgUnits" :key="o.Id" class="role-item">
          <input type="checkbox" :checked="o.Id in orgSelection" @change="toggleOrg(o.Id)" />
          {{ o.Name }}
        </label>
      </div>
      <button class="primary-btn" @click="saveOrgAccess">Сохранить доступ</button>
    </section>

    <section class="card">
      <h3>Доступ по проектам</h3>
      <p class="hint">Сверх проектов, куда пользователь назначен через Assignments (§15 ТЗ) — например, для роли без назначения на проект.</p>
      <div class="role-list">
        <label v-for="p in allProjects" :key="p.Id" class="role-item">
          <input type="checkbox" :checked="p.Id in projectSelection" @change="toggleProject(p.Id)" />
          {{ p.Name }}
        </label>
      </div>
      <button class="primary-btn" @click="saveProjectAccess">Сохранить доступ</button>
    </section>

    <section class="card">
      <h3>Персональные исключения прав</h3>
      <table class="grid">
        <thead>
          <tr><th>Модуль</th><th>Действие</th><th>Эффект</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="o in detail.PermissionOverrides" :key="`${o.Module}-${o.Action}`">
            <td>{{ o.Module }}</td>
            <td>{{ o.Action }}</td>
            <td>{{ o.Effect === "GRANT" ? "Разрешить" : "Запретить" }}</td>
            <td><button class="link-btn" @click="removeOverride(o.Module, o.Action)">Убрать</button></td>
          </tr>
        </tbody>
      </table>
      <div class="override-form">
        <input v-model="overrideForm.Module" placeholder="Модуль (напр. EMPLOYEES)" />
        <select v-model="overrideForm.Action">
          <option value="VIEW">VIEW</option>
          <option value="CREATE">CREATE</option>
          <option value="UPDATE">UPDATE</option>
          <option value="DELETE">DELETE</option>
          <option value="IMPORT">IMPORT</option>
          <option value="EXPORT">EXPORT</option>
        </select>
        <select v-model="overrideForm.Effect">
          <option value="GRANT">Разрешить</option>
          <option value="DENY">Запретить</option>
        </select>
        <input v-model="overrideForm.Reason" placeholder="Причина" />
        <button class="primary-btn" @click="addOverride">Добавить</button>
      </div>
    </section>

    <p v-if="message" class="save-message">{{ message }}</p>
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
.page h2 {
  margin: 0 0 1rem;
}
.email {
  color: #94a3b8;
  font-weight: 400;
  font-size: 0.9rem;
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
.hint {
  margin: -0.4rem 0 0.75rem;
  font-size: 0.8rem;
  color: #94a3b8;
}
.role-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
  max-height: 240px;
  overflow-y: auto;
}
.role-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: #334155;
}
.expiry-input {
  margin-left: auto;
  padding: 0.2rem 0.4rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.8rem;
}
.primary-btn {
  padding: 0.5rem 1.1rem;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}
.grid {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}
.grid th,
.grid td {
  text-align: left;
  padding: 0.4rem 0.6rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.85rem;
}
.link-btn {
  border: none;
  background: none;
  color: #dc2626;
  cursor: pointer;
  padding: 0;
  font-size: 0.85rem;
}
.override-form {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.override-form input,
.override-form select {
  padding: 0.4rem 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.85rem;
}
.save-message {
  color: #16a34a;
  font-size: 0.85rem;
}
</style>
