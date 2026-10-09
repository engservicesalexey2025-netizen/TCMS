<script setup>
import Button from "primevue/button";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import apiClient from "../api/client";
import { useAuthStore } from "../stores/auth";
import { isoToDisplayDate } from "../utils/date";
import CreatableSelect from "./CreatableSelect.vue";
import DateInput from "./DateInput.vue";
import PhoneInput from "./PhoneInput.vue";

const props = defineProps({
  resource: { type: String, required: true },
  title: { type: String, required: true },
  columns: { type: Array, required: true }, // [{ field, header, type?: 'badge', map? }]
  formFields: { type: Array, required: true }, // [{ field, label, type, options }]
  // {create,edit,delete,import,export} — по умолчанию всё разрешено, чтобы
  // вызовы без явного prop сохраняли сегодняшнее поведение (обратная
  // совместимость на время поэтапной миграции экранов на права, §14 ТЗ).
  permissions: {
    type: Object,
    default: () => ({ create: true, edit: true, delete: true, import: true, export: true }),
  },
  // Модуль Column-Level Security (напр. "EMPLOYEES") — если задан, колонки
  // таблицы и поля формы фильтруются через auth.canSeeColumn(module, field);
  // если не задан — поведение как раньше (ничего не фильтруется).
  columnPermissionModule: { type: String, default: null },
  importResource: { type: String, default: null }, // entity_type for /imports/:entityType
  rowLink: { type: String, default: null }, // e.g. "/employees" -> row click navigates to `${rowLink}/${row.Id}`
  editLink: { type: String, default: null }, // e.g. "/employees" -> "Изменить" navigates here instead of opening the quick dialog
  exportResource: { type: Boolean, default: false }, // renders "Экспорт в Excel" hitting `${resource}/export`
  extraParams: { type: Object, default: () => ({}) }, // extra query params merged into the list request, e.g. quick-filter chips
  rowClass: { type: Function, default: null }, // (row) => className, e.g. deadline-based row highlighting
});

const auth = useAuthStore();

const emit = defineEmits(["changed"]);

const router = useRouter();

function goToImport() {
  router.push(`/imports/${props.importResource}`);
}

function goToRow(row) {
  if (props.rowLink) {
    router.push(`${props.rowLink}/${row.Id}`);
  }
}

const items = ref([]);
const total = ref(0);
const skip = ref(0);
const limit = ref(20);
const search = ref("");
const loading = ref(false);
const showArchived = ref(false);

const dialogVisible = ref(false);
const editingId = ref(null);
const form = reactive({});
const formError = ref("");

async function load() {
  loading.value = true;
  try {
    const { data } = await apiClient.get(props.resource, {
      params: {
        skip: skip.value,
        limit: limit.value,
        search: search.value || undefined,
        include_archived: showArchived.value,
        ...props.extraParams,
      },
    });
    items.value = data.items;
    total.value = data.total;
  } finally {
    loading.value = false;
  }
}

watch(
  () => props.extraParams,
  () => {
    skip.value = 0;
    load();
  },
  { deep: true },
);

let searchDebounceTimer = null;
function onSearchInput() {
  skip.value = 0;
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(load, 300);
}

function clearSearch() {
  search.value = "";
  skip.value = 0;
  load();
}

async function exportToExcel() {
  const response = await apiClient.get(`${props.resource}/export`, {
    params: {
      search: search.value || undefined,
      include_archived: showArchived.value,
    },
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = `${props.resource.replace(/^\//, "").replace(/\//g, "_")}_export.xlsx`;
  link.click();
  window.URL.revokeObjectURL(url);
}

function resetForm() {
  visibleFormFields.value.forEach((f) => {
    form[f.field] = f.default ?? null;
  });
}

function openCreate() {
  editingId.value = null;
  formError.value = "";
  resetForm();
  dialogVisible.value = true;
}

function openEdit(row) {
  if (props.editLink) {
    router.push(`${props.editLink}/${row.Id}`);
    return;
  }
  editingId.value = row.Id;
  formError.value = "";
  visibleFormFields.value.forEach((f) => {
    form[f.field] = row[f.field] ?? null;
  });
  dialogVisible.value = true;
}

async function save() {
  formError.value = "";
  try {
    if (editingId.value) {
      await apiClient.patch(`${props.resource}/${editingId.value}`, form);
    } else {
      await apiClient.post(props.resource, form);
    }
    dialogVisible.value = false;
    await load();
    emit("changed");
  } catch (e) {
    formError.value = e.response?.data?.detail || "Ошибка сохранения";
  }
}

async function toggleArchive(row) {
  const action = row.IsActive ? "archive" : "restore";
  if (action === "archive" && !window.confirm("Вы точно хотите отправить запись в архив?")) {
    return;
  }
  await apiClient.post(`${props.resource}/${row.Id}/${action}`);
  await load();
  emit("changed");
}

const columnsStorageKey = `entitytable_columns_${props.resource}`;
const columnPickerOpen = ref(false);
const hiddenFields = ref(new Set(JSON.parse(localStorage.getItem(columnsStorageKey) || "[]")));

// Право на столбец (§14 ТЗ) — декларативно по auth.canSeeColumn, а не по
// тому, есть ли ключ у загруженных строк (иначе пустая страница выглядела
// бы как "все столбцы скрыты").
const permittedColumns = computed(() => {
  if (!props.columnPermissionModule) return props.columns;
  return props.columns.filter((c) => auth.canSeeColumn(props.columnPermissionModule, c.field));
});
const visibleColumns = computed(() => permittedColumns.value.filter((c) => !hiddenFields.value.has(c.field)));
const visibleFormFields = computed(() => {
  if (!props.columnPermissionModule) return props.formFields;
  return props.formFields.filter((f) => auth.canSeeColumn(props.columnPermissionModule, f.field));
});

function toggleColumn(field) {
  const next = new Set(hiddenFields.value);
  if (next.has(field)) {
    next.delete(field);
  } else {
    next.add(field);
  }
  hiddenFields.value = next;
  localStorage.setItem(columnsStorageKey, JSON.stringify([...next]));
}

const dateFields = computed(
  () => new Set(props.formFields.filter((f) => f.type === "date").map((f) => f.field)),
);

function fieldLabel(row, col) {
  const value = row[col.field];
  if (col.format) {
    return col.format(value, row);
  }
  if (col.options) {
    return col.options.find((o) => o.value === value)?.label ?? value;
  }
  if (dateFields.value.has(col.field)) {
    return isoToDisplayDate(value) || value;
  }
  return value;
}

function badgeInfo(row, col) {
  const value = col.badgeKey ? col.badgeKey(row) : row[col.field];
  return col.map?.[value] || { label: value, color: "#94a3b8" };
}

function handleOutsideClick(event) {
  if (columnPickerOpen.value && !event.target.closest(".column-picker")) {
    columnPickerOpen.value = false;
  }
}

onMounted(() => {
  load();
  document.addEventListener("click", handleOutsideClick);
});
onUnmounted(() => document.removeEventListener("click", handleOutsideClick));

defineExpose({ load });
</script>

<template>
  <div>
    <div class="toolbar">
      <h2>{{ title }}</h2>
      <div class="spacer" />
      <div class="search-box">
        <input v-model="search" placeholder="Поиск..." @input="onSearchInput" />
        <button v-if="search" class="clear-search-btn" title="Очистить" @click="clearSearch">×</button>
      </div>
      <label class="archived-toggle">
        <input v-model="showArchived" type="checkbox" @change="load" />
        Архив
      </label>
      <div class="column-picker">
        <Button
          label="Столбцы"
          icon="pi pi-table"
          severity="secondary"
          text
          @click="columnPickerOpen = !columnPickerOpen"
        />
        <div v-if="columnPickerOpen" class="column-picker-dropdown">
          <label v-for="col in permittedColumns" :key="col.field" class="column-picker-item">
            <input
              type="checkbox"
              :checked="!hiddenFields.has(col.field)"
              @change="toggleColumn(col.field)"
            />
            {{ col.header }}
          </label>
        </div>
      </div>
      <Button
        v-if="permissions.import && importResource"
        label="Импорт"
        icon="pi pi-upload"
        severity="secondary"
        @click="goToImport"
      />
      <Button
        v-if="exportResource && permissions.export"
        label="Экспорт в Excel"
        icon="pi pi-file-excel"
        severity="secondary"
        @click="exportToExcel"
      />
      <Button v-if="permissions.create" label="Добавить" icon="pi pi-plus" @click="openCreate" />
    </div>

    <table class="grid">
      <thead>
        <tr>
          <th v-for="col in visibleColumns" :key="col.field">{{ col.header }}</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in items"
          :key="row.Id"
          :class="[{ inactive: !row.IsActive, clickable: !!rowLink }, rowClass ? rowClass(row) : '']"
          @click="goToRow(row)"
        >
          <td v-for="col in visibleColumns" :key="col.field">
            <span
              v-if="col.type === 'badge'"
              class="status-badge"
              :style="{ background: badgeInfo(row, col).color }"
            >
              {{ badgeInfo(row, col).label }}
            </span>
            <template v-else>{{ fieldLabel(row, col) }}</template>
          </td>
          <td class="actions">
            <button v-if="permissions.edit" class="link-btn" @click.stop="openEdit(row)">Изменить</button>
            <button v-if="permissions.delete" class="link-btn" @click.stop="toggleArchive(row)">
              {{ row.IsActive ? "В архив" : "Восстановить" }}
            </button>
          </td>
        </tr>
        <tr v-if="!loading && items.length === 0">
          <td :colspan="visibleColumns.length + 1" class="empty">Нет записей</td>
        </tr>
      </tbody>
    </table>

    <div class="pager">
      <button :disabled="skip === 0" @click="skip = Math.max(0, skip - limit); load()">← Назад</button>
      <span>{{ skip + 1 }}–{{ Math.min(skip + limit, total) }} из {{ total }}</span>
      <button :disabled="skip + limit >= total" @click="skip += limit; load()">Вперёд →</button>
    </div>

    <Dialog v-model:visible="dialogVisible" modal :header="editingId ? 'Изменить запись' : 'Новая запись'" :style="{ width: '28rem' }">
      <div class="form">
        <label v-for="f in visibleFormFields" :key="f.field" class="form-field">
          {{ f.label }}
          <select v-if="f.type === 'select'" v-model="form[f.field]">
            <option value="" disabled>Выберите...</option>
            <option v-for="o in f.options" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
          <CreatableSelect
            v-else-if="f.type === 'creatable-select'"
            v-model="form[f.field]"
            :options="f.options"
            :create-endpoint="f.createEndpoint"
            @created="(opt) => f.onCreated && f.onCreated(opt)"
            @deleted="(id) => f.onDeleted && f.onDeleted(id)"
          />
          <DateInput v-else-if="f.type === 'date'" v-model="form[f.field]" />
          <input v-else-if="f.type === 'number'" v-model.number="form[f.field]" type="number" step="0.01" />
          <PhoneInput v-else-if="f.type === 'phone'" v-model="form[f.field]" />
          <InputText v-else v-model="form[f.field]" />
        </label>
        <p v-if="formError" class="error">{{ formError }}</p>
      </div>
      <template #footer>
        <Button label="Отмена" text @click="dialogVisible = false" />
        <Button label="Сохранить" @click="save" />
      </template>
    </Dialog>
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
.search-box {
  position: relative;
  display: flex;
  align-items: center;
}
.search-box input {
  padding: 0.4rem 1.8rem 0.4rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}
.clear-search-btn {
  position: absolute;
  right: 0.4rem;
  border: none;
  background: none;
  color: #94a3b8;
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
  padding: 0;
}
.clear-search-btn:hover {
  color: #475569;
}
.archived-toggle {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #475569;
}
.column-picker {
  position: relative;
}
.column-picker-dropdown {
  position: absolute;
  z-index: 20;
  top: calc(100% + 2px);
  right: 0;
  min-width: 220px;
  max-height: 320px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
  padding: 0.5rem;
}
.column-picker-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.3rem 0.4rem;
  font-size: 0.85rem;
  color: #334155;
  cursor: pointer;
  white-space: nowrap;
}
.column-picker-item:hover {
  background: #f1f5f9;
  border-radius: 4px;
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
.grid tr.inactive {
  color: #94a3b8;
  background: #f8fafc;
}
.grid tr.clickable {
  cursor: pointer;
}
.grid tr.clickable:hover {
  background: #f8fafc;
}
.grid tr.row-warning {
  background: #fef9c3;
}
.grid tr.row-warning:hover {
  background: #fef08a;
}
.grid tr.row-danger {
  background: #fecaca;
}
.grid tr.row-danger:hover {
  background: #fca5a5;
}
.status-badge {
  display: inline-block;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  color: #fff;
  font-size: 0.8rem;
  white-space: nowrap;
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
.pager {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.75rem;
  font-size: 0.85rem;
  color: #475569;
}
.form {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
}
.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #334155;
}
.form-field select,
.form-field input:not([type="checkbox"]) {
  padding: 0.5rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
}
</style>
