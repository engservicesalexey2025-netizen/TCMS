<script setup>
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import apiClient from "../../api/client";

const route = useRoute();
const router = useRouter();
const roleId = route.params.id;

const activeTab = ref("modules");
const role = ref(null);
const permissions = ref([]); // [{Module, Action, Granted}]
const saving = ref(false);
const saveMessage = ref("");

const ACTIONS = ["VIEW", "CREATE", "UPDATE", "DELETE", "IMPORT", "EXPORT"];
const ACTION_LABELS = {
  VIEW: "Просмотр", CREATE: "Создание", UPDATE: "Изменение",
  DELETE: "Удаление", IMPORT: "Импорт", EXPORT: "Экспорт",
};

const modules = computed(() => {
  const set = new Set(permissions.value.map((p) => p.Module));
  return [...set].sort();
});

function isGranted(module, action) {
  return permissions.value.some((p) => p.Module === module && p.Action === action && p.Granted);
}

function hasPermission(module, action) {
  return permissions.value.some((p) => p.Module === module && p.Action === action);
}

function toggle(module, action) {
  const row = permissions.value.find((p) => p.Module === module && p.Action === action);
  if (row) row.Granted = !row.Granted;
}

async function loadPermissions() {
  const { data } = await apiClient.get(`/roles/${roleId}/permissions`);
  permissions.value = data;
}

async function loadRole() {
  const { data } = await apiClient.get("/roles", { params: { limit: 100 } });
  role.value = data.items.find((r) => r.Id === roleId) || null;
}

async function savePermissions() {
  saving.value = true;
  saveMessage.value = "";
  try {
    const payload = permissions.value.map((p) => ({ Module: p.Module, Action: p.Action, Granted: p.Granted }));
    const { data } = await apiClient.put(`/roles/${roleId}/permissions`, payload);
    permissions.value = data;
    saveMessage.value = "Сохранено";
  } finally {
    saving.value = false;
  }
}

// --- Столбцы ---
const ENTITIES = ["Employees"];
const FIELDS_BY_ENTITY = {
  Employees: ["IIN", "PersonalPhone", "Salary", "BirthDate"],
};
const FIELD_LABELS = { IIN: "ИИН", PersonalPhone: "Личный телефон", Salary: "Оклад", BirthDate: "Дата рождения" };
const selectedEntity = ref(ENTITIES[0]);
const columnModes = ref({}); // { field: mode }
const columnSaveMessage = ref("");

async function loadColumnPermissions() {
  const { data } = await apiClient.get(`/roles/${roleId}/column-permissions`, {
    params: { entity: selectedEntity.value },
  });
  const modes = {};
  for (const field of FIELDS_BY_ENTITY[selectedEntity.value]) modes[field] = "FULL";
  for (const row of data) modes[row.FieldName] = row.Mode;
  columnModes.value = modes;
}

async function saveColumnPermissions() {
  const fields = Object.entries(columnModes.value).map(([FieldName, Mode]) => ({ FieldName, Mode }));
  await apiClient.put(`/roles/${roleId}/column-permissions`, { EntityName: selectedEntity.value, Fields: fields });
  columnSaveMessage.value = "Сохранено";
}

function selectTab(tab) {
  activeTab.value = tab;
  if (tab === "columns" && Object.keys(columnModes.value).length === 0) loadColumnPermissions();
}

onMounted(async () => {
  await Promise.all([loadRole(), loadPermissions()]);
});
</script>

<template>
  <div class="editor">
    <button class="back-btn" @click="router.push({ name: 'admin-roles' })">← К списку ролей</button>
    <h2 v-if="role">{{ role.Name }} <span class="code">({{ role.Code }})</span></h2>

    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'modules' }]" @click="selectTab('modules')">Модули и разделы</button>
      <button :class="['tab-btn', { active: activeTab === 'columns' }]" @click="selectTab('columns')">Столбцы</button>
    </div>

    <section v-if="activeTab === 'modules'" class="card">
      <table class="matrix">
        <thead>
          <tr>
            <th>Модуль</th>
            <th v-for="a in ACTIONS" :key="a">{{ ACTION_LABELS[a] }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in modules" :key="m">
            <td>{{ m }}</td>
            <td v-for="a in ACTIONS" :key="a" class="check-cell">
              <input
                v-if="hasPermission(m, a)"
                type="checkbox"
                :checked="isGranted(m, a)"
                @change="toggle(m, a)"
              />
            </td>
          </tr>
        </tbody>
      </table>
      <div class="save-row">
        <button class="primary-btn" :disabled="saving" @click="savePermissions">
          {{ saving ? "Сохранение..." : "Сохранить" }}
        </button>
        <span v-if="saveMessage" class="save-message">{{ saveMessage }}</span>
      </div>
    </section>

    <section v-else-if="activeTab === 'columns'" class="card">
      <label class="field">
        Раздел
        <select v-model="selectedEntity" @change="loadColumnPermissions">
          <option v-for="e in ENTITIES" :key="e" :value="e">{{ e }}</option>
        </select>
      </label>
      <table class="matrix">
        <thead>
          <tr>
            <th>Поле</th>
            <th>Режим</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="field in FIELDS_BY_ENTITY[selectedEntity]" :key="field">
            <td>{{ FIELD_LABELS[field] || field }}</td>
            <td>
              <select v-model="columnModes[field]">
                <option value="FULL">Видно полностью</option>
                <option value="MASKED">Маскировать</option>
                <option value="HIDDEN">Скрыть</option>
              </select>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="save-row">
        <button class="primary-btn" @click="saveColumnPermissions">Сохранить</button>
        <span v-if="columnSaveMessage" class="save-message">{{ columnSaveMessage }}</span>
      </div>
    </section>
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
.editor h2 {
  margin: 0 0 1rem;
}
.code {
  color: #94a3b8;
  font-weight: 400;
  font-size: 0.9rem;
}
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.tab-btn {
  border: 1px solid #cbd5e1;
  background: #fff;
  padding: 0.4rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  color: #334155;
}
.tab-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}
.card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.5rem;
}
.matrix {
  width: 100%;
  border-collapse: collapse;
}
.matrix th,
.matrix td {
  text-align: left;
  padding: 0.5rem 0.7rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.85rem;
}
.check-cell {
  text-align: center;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #334155;
  margin-bottom: 1rem;
  max-width: 240px;
}
.field select,
select {
  padding: 0.4rem 0.5rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}
.save-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 1rem;
}
.primary-btn {
  padding: 0.55rem 1.2rem;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}
.save-message {
  color: #16a34a;
  font-size: 0.85rem;
}
</style>
