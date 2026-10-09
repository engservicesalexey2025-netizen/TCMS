<script setup>
import { computed, onMounted, reactive, ref, watch } from "vue";
import apiClient from "../api/client";
import OrgUnitCard from "../components/OrgUnitCard.vue";
import OrgUnitFullList from "../components/OrgUnitFullList.vue";
import OrgUnitTree from "../components/OrgUnitTree.vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const canCreate = computed(() => auth.can("ORG_UNITS", "CREATE"));
const canExport = computed(() => auth.can("ORG_UNITS", "EXPORT"));
const canImport = computed(() => auth.can("ORG_UNITS", "IMPORT"));
const exporting = ref(false);
const exportingSpecialists = ref(false);
const importingSpecialists = ref(false);
const importResult = ref(null);
const importError = ref("");

const activeTab = ref("tree");
const flatUnits = ref([]);
const fullTree = ref([]);
const selectedId = ref(null);
const creating = ref(false);
const createForm = reactive({ Name: "", UnitType: "DIVISION", Code: "", ParentOrgUnitId: null });
const createError = ref("");

const TYPE_LABELS = {
  DIVISION: "Дивизион",
  CITY: "Город",
  DEPARTMENT: "Управление",
  GROUP: "Группа",
};
const typeOptions = Object.entries(TYPE_LABELS).map(([value, label]) => ({ value, label }));

// Жёсткий маршрут иерархии (тот же список, что и в backend-валидации
// app/api/v1/org.py::ORG_UNIT_ALLOWED_PARENT_TYPES) — форма создания сразу
// предлагает только допустимых родителей, чтобы не ловить ошибку 400.
const ALLOWED_PARENT_TYPES = {
  DIVISION: [],
  CITY: ["DIVISION"],
  DEPARTMENT: ["CITY"],
  GROUP: ["DEPARTMENT"],
};

const parentOptions = computed(() => {
  const allowed = ALLOWED_PARENT_TYPES[createForm.UnitType] || [];
  return flatUnits.value
    .filter((u) => allowed.includes(u.UnitType))
    .map((u) => ({ value: u.Id, label: u.Name }));
});

watch(
  () => createForm.UnitType,
  () => {
    createForm.ParentOrgUnitId = null;
  },
);

const tree = computed(() => {
  const byParent = new Map();
  for (const u of flatUnits.value) {
    const key = u.ParentOrgUnitId || "root";
    if (!byParent.has(key)) byParent.set(key, []);
    byParent.get(key).push(u);
  }
  function attach(nodes) {
    return nodes.map((n) => ({ ...n, Children: attach(byParent.get(n.Id) || []) }));
  }
  return attach(byParent.get("root") || []);
});

async function loadTree() {
  const { data } = await apiClient.get("/org-units/tree");
  flatUnits.value = data;
}

async function loadFullTree() {
  const { data } = await apiClient.get("/org-units/full-tree");
  fullTree.value = data;
}

function selectUnit(id) {
  selectedId.value = id;
}

function selectFromList(id) {
  activeTab.value = "tree";
  selectUnit(id);
  if (flatUnits.value.length === 0) loadTree();
}

async function exportToExcel() {
  exporting.value = true;
  try {
    const response = await apiClient.get("/org-units/export", { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.download = "org_units_export.xlsx";
    link.click();
    window.URL.revokeObjectURL(url);
  } finally {
    exporting.value = false;
  }
}

async function exportSpecialists() {
  exportingSpecialists.value = true;
  try {
    const response = await apiClient.get("/org-units/export-specialists", { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.download = "specialists_export.xlsx";
    link.click();
    window.URL.revokeObjectURL(url);
  } finally {
    exportingSpecialists.value = false;
  }
}

async function importSpecialists(event) {
  const file = event.target.files[0];
  if (!file) return;
  importingSpecialists.value = true;
  importError.value = "";
  importResult.value = null;
  try {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await apiClient.post("/org-units/import-specialists", formData);
    importResult.value = data;
    await loadTree();
    if (activeTab.value === "list") await loadFullTree();
  } catch (e) {
    importError.value = e.response?.data?.detail || "Ошибка загрузки файла";
  } finally {
    importingSpecialists.value = false;
    event.target.value = "";
  }
}

function selectTab(tab) {
  activeTab.value = tab;
  // Всегда перезагружаем — данные могли поменяться во вкладке «Дерево»
  // (создание/архивирование/назначение руководителя).
  if (tab === "list") loadFullTree();
}

async function submitCreate() {
  createError.value = "";
  try {
    const { data } = await apiClient.post("/org-units", {
      Name: createForm.Name,
      UnitType: createForm.UnitType,
      Code: createForm.Code || null,
      ParentOrgUnitId: createForm.ParentOrgUnitId,
    });
    await loadTree();
    selectedId.value = data.Id;
    creating.value = false;
    Object.assign(createForm, { Name: "", UnitType: "DIVISION", Code: "", ParentOrgUnitId: null });
  } catch (e) {
    createError.value = e.response?.data?.detail || "Ошибка создания";
  }
}

onMounted(loadTree);
</script>

<template>
  <div class="org-units">
    <div class="header">
      <h2>Организационная структура</h2>
      <div class="header-actions">
        <button v-if="canExport" class="secondary-btn" :disabled="exporting" @click="exportToExcel">
          {{ exporting ? "Экспорт..." : "Экспорт в Excel" }}
        </button>
        <button
          v-if="canExport"
          class="secondary-btn"
          :disabled="exportingSpecialists"
          @click="exportSpecialists"
        >
          {{ exportingSpecialists ? "Экспорт..." : "Экспорт специалистов" }}
        </button>
        <label v-if="canImport" class="secondary-btn file-btn">
          {{ importingSpecialists ? "Загрузка..." : "Импорт специалистов" }}
          <input
            type="file"
            accept=".xlsx"
            :disabled="importingSpecialists"
            hidden
            @change="importSpecialists"
          />
        </label>
        <button v-if="canCreate" class="primary-btn" @click="creating = !creating">
          {{ creating ? "Отмена" : "+ Создать подразделение" }}
        </button>
      </div>
    </div>

    <div v-if="importError" class="import-result error-panel">
      {{ importError }}
    </div>
    <div v-if="importResult" class="import-result">
      <div class="import-summary">
        Назначено: {{ importResult.Assigned }} · Без изменений: {{ importResult.Unchanged }} ·
        Ошибок: {{ importResult.Failed }}
        <button class="link-btn" @click="importResult = null">Закрыть</button>
      </div>
      <ul v-if="importResult.Errors.length" class="import-errors">
        <li v-for="err in importResult.Errors" :key="err.RowNumber">
          Строка {{ err.RowNumber }}: {{ err.Message }}
        </li>
      </ul>
    </div>

    <div v-if="creating" class="create-form">
      <label class="field">
        Название
        <input v-model="createForm.Name" type="text" />
      </label>
      <label class="field">
        Тип
        <select v-model="createForm.UnitType">
          <option v-for="o in typeOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
        </select>
      </label>
      <label class="field">
        Код
        <input v-model="createForm.Code" type="text" />
      </label>
      <label v-if="createForm.UnitType === 'DIVISION'" class="field">
        Родительское подразделение
        <span class="readonly-value">— нет, Дивизион — верхний уровень —</span>
      </label>
      <label v-else class="field">
        Родительское подразделение
        <select v-model="createForm.ParentOrgUnitId">
          <option :value="null" disabled>— выберите —</option>
          <option v-for="o in parentOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
        </select>
      </label>
      <button class="primary-btn" @click="submitCreate">Создать</button>
      <p v-if="createError" class="error">{{ createError }}</p>
    </div>

    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'tree' }]" @click="selectTab('tree')">
        Дерево
      </button>
      <button :class="['tab-btn', { active: activeTab === 'list' }]" @click="selectTab('list')">
        Список
      </button>
    </div>

    <div v-if="activeTab === 'tree'" class="layout">
      <aside class="tree-panel">
        <OrgUnitTree :nodes="tree" :selected-id="selectedId" @select="selectUnit" />
        <p v-if="flatUnits.length === 0" class="empty">Подразделений пока нет</p>
      </aside>
      <main class="card-panel">
        <OrgUnitCard
          v-if="selectedId"
          :unit-id="selectedId"
          :all-units="flatUnits"
          @changed="loadTree"
          @select="selectUnit"
          @deleted="selectedId = null"
        />
        <p v-else class="empty">Выберите подразделение слева, чтобы увидеть карточку</p>
      </main>
    </div>

    <div v-else class="list-panel">
      <OrgUnitFullList :nodes="fullTree" @select="selectFromList" />
      <p v-if="fullTree.length === 0" class="empty">Подразделений пока нет</p>
    </div>
  </div>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
.header h2 {
  margin: 0;
}
.create-form {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #334155;
}
.field input,
.field select {
  padding: 0.5rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
}
.readonly-value {
  padding: 0.5rem 0;
  color: #64748b;
  font-size: 0.85rem;
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
.list-panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.25rem;
  overflow-x: auto;
}
.layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 1.25rem;
  align-items: start;
}
.tree-panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem;
}
.card-panel {
  min-width: 0;
}
.header-actions {
  display: flex;
  gap: 0.75rem;
}
.primary-btn {
  padding: 0.5rem 1.1rem;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
  font-size: 0.85rem;
  height: fit-content;
}
.secondary-btn {
  padding: 0.5rem 1.1rem;
  border: 1px solid #2563eb;
  border-radius: 6px;
  background: #fff;
  color: #2563eb;
  cursor: pointer;
  font-size: 0.85rem;
  height: fit-content;
}
.empty {
  color: #94a3b8;
  font-size: 0.85rem;
  text-align: center;
  padding: 1rem 0;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
  width: 100%;
}
.file-btn {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
}
.import-result {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.85rem 1.1rem;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: #334155;
}
.import-result.error-panel {
  border-color: #fecaca;
  background: #fef2f2;
  color: #dc2626;
}
.import-summary {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.import-errors {
  margin: 0.6rem 0 0;
  padding-left: 1.2rem;
  color: #dc2626;
  max-height: 200px;
  overflow-y: auto;
}
.link-btn {
  border: none;
  background: none;
  color: #2563eb;
  cursor: pointer;
  padding: 0;
  font-size: 0.85rem;
}
</style>
