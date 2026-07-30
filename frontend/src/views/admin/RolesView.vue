<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import apiClient from "../../api/client";

const router = useRouter();
const roles = ref([]);
const loading = ref(false);

const createDialog = ref(false);
const createForm = reactive({ Code: "", Name: "" });
const createError = ref("");

const cloneDialog = ref(false);
const cloneSourceId = ref(null);
const cloneForm = reactive({ NewCode: "", NewName: "" });
const cloneError = ref("");

async function load() {
  loading.value = true;
  try {
    const { data } = await apiClient.get("/roles", { params: { limit: 100 } });
    roles.value = data.items;
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  createForm.Code = "";
  createForm.Name = "";
  createError.value = "";
  createDialog.value = true;
}

async function submitCreate() {
  createError.value = "";
  try {
    await apiClient.post("/roles", createForm);
    createDialog.value = false;
    await load();
  } catch (e) {
    createError.value = e.response?.data?.detail || "Не удалось создать роль";
  }
}

function openClone(role) {
  cloneSourceId.value = role.Id;
  cloneForm.NewCode = "";
  cloneForm.NewName = "";
  cloneError.value = "";
  cloneDialog.value = true;
}

async function submitClone() {
  cloneError.value = "";
  try {
    await apiClient.post(`/roles/${cloneSourceId.value}/clone`, cloneForm);
    cloneDialog.value = false;
    await load();
  } catch (e) {
    cloneError.value = e.response?.data?.detail || "Не удалось клонировать роль";
  }
}

function openEditor(role) {
  router.push({ name: "admin-role-editor", params: { id: role.Id } });
}

onMounted(load);
</script>

<template>
  <div>
    <div class="toolbar">
      <h2>Роли и права</h2>
      <div class="spacer" />
      <button class="primary-btn" @click="openCreate">Создать роль</button>
    </div>

    <table class="grid">
      <thead>
        <tr>
          <th>Код</th>
          <th>Название</th>
          <th>Системная</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in roles" :key="r.Id">
          <td>{{ r.Code }}</td>
          <td>{{ r.Name }}</td>
          <td>{{ r.IsSystem ? "Да" : "" }}</td>
          <td class="actions">
            <button class="link-btn" @click="openEditor(r)">Права</button>
            <button class="link-btn" @click="openClone(r)">Клонировать</button>
          </td>
        </tr>
        <tr v-if="!loading && roles.length === 0">
          <td colspan="4" class="empty">Ролей нет</td>
        </tr>
      </tbody>
    </table>

    <div v-if="createDialog" class="modal-backdrop" @click.self="createDialog = false">
      <div class="modal">
        <h3>Новая роль</h3>
        <label class="field">
          Код
          <input v-model="createForm.Code" type="text" placeholder="LABORATORY" />
        </label>
        <label class="field">
          Название
          <input v-model="createForm.Name" type="text" placeholder="Лаборатория" />
        </label>
        <p v-if="createError" class="error">{{ createError }}</p>
        <div class="modal-actions">
          <button class="secondary-btn" @click="createDialog = false">Отмена</button>
          <button class="primary-btn" @click="submitCreate">Создать</button>
        </div>
      </div>
    </div>

    <div v-if="cloneDialog" class="modal-backdrop" @click.self="cloneDialog = false">
      <div class="modal">
        <h3>Клонировать роль (шаблон)</h3>
        <label class="field">
          Код новой роли
          <input v-model="cloneForm.NewCode" type="text" />
        </label>
        <label class="field">
          Название новой роли
          <input v-model="cloneForm.NewName" type="text" />
        </label>
        <p v-if="cloneError" class="error">{{ cloneError }}</p>
        <div class="modal-actions">
          <button class="secondary-btn" @click="cloneDialog = false">Отмена</button>
          <button class="primary-btn" @click="submitClone">Клонировать</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.toolbar h2 {
  margin: 0;
}
.spacer {
  flex: 1;
}
.grid {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}
.grid th,
.grid td {
  text-align: left;
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.9rem;
}
.actions {
  white-space: nowrap;
}
.link-btn {
  border: none;
  background: none;
  color: #2563eb;
  cursor: pointer;
  padding: 0;
  margin-right: 0.75rem;
  font-size: 0.85rem;
}
.empty {
  text-align: center;
  color: #94a3b8;
  padding: 1.5rem;
}
.primary-btn,
.secondary-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
}
.primary-btn {
  background: #2563eb;
  color: #fff;
}
.secondary-btn {
  background: #e2e8f0;
  color: #334155;
}
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
}
.modal {
  background: #fff;
  border-radius: 10px;
  padding: 1.5rem;
  width: 340px;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}
.modal h3 {
  margin: 0;
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
  margin: 0;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
}
</style>
