<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import apiClient from "../api/client";
import CreatableSelect from "../components/CreatableSelect.vue";
import ProjectDocumentsTab from "../components/ProjectDocumentsTab.vue";
import { PROJECT_STATUS } from "../constants/projectStatus";

const route = useRoute();
const router = useRouter();
const projectId = route.params.id;

const activeTab = ref("main");
const project = ref(null);
const form = reactive({});
const saveError = ref("");
const saving = ref(false);

const cities = ref([]);
const orgUnits = ref([]);
const projectTypes = ref([]);
const projectStages = ref([]);
const contours = ref([]);
const controlSystems = ref([]);
const contractors = ref([]);

const historyItems = ref([]);
const historyTotal = ref(0);
const historySkip = ref(0);
const historyLimit = ref(20);

const cityOptions = computed(() => cities.value.map((c) => ({ label: c.Name, value: c.Id })));
const orgUnitOptions = computed(() => orgUnits.value.map((u) => ({ label: u.Name, value: u.Id })));
const projectTypeOptions = computed(() =>
  projectTypes.value.map((t) => ({ label: t.Name, value: t.Id })),
);
const projectStageOptions = computed(() =>
  projectStages.value.map((s) => ({ label: s.Name, value: s.Id })),
);
const contourOptions = computed(() => contours.value.map((c) => ({ label: c.Name, value: c.Id })));
const controlSystemOptions = computed(() =>
  controlSystems.value.map((s) => ({ label: s.Name, value: s.Id })),
);
const contractorOptions = computed(() =>
  contractors.value.map((c) => ({ label: c.Name, value: c.Id })),
);
const statusOptions = Object.entries(PROJECT_STATUS).map(([value, s]) => ({
  label: s.label,
  value,
}));

async function loadProject() {
  const { data } = await apiClient.get(`/projects/${projectId}`);
  project.value = data;
  Object.assign(form, {
    Name: data.Name,
    CityId: data.CityId,
    Address: data.Address,
    Description: data.Description,
    OrgUnitId: data.OrgUnitId,
    ProjectTypeId: data.ProjectTypeId,
    ProjectStageId: data.ProjectStageId,
    ContourId: data.ContourId,
    ControlSystemId: data.ControlSystemId,
    Status: data.Status,
    DeveloperId: data.DeveloperId,
    ContractorId: data.ContractorId,
    GeneralContractorId: data.GeneralContractorId,
    SubcontractorId: data.SubcontractorId,
    ContractNumber: data.ContractNumber,
    Area: data.Area,
    Cost: data.Cost,
    GisLink: data.GisLink,
    GaskTicketNumber: data.GaskTicketNumber,
    GaskNotificationNumber: data.GaskNotificationNumber,
    GaskTicketDate: data.GaskTicketDate,
    GaskTicketExpiryDate: data.GaskTicketExpiryDate,
    ActualEndDate: data.ActualEndDate,
    Comment: data.Comment,
  });
}

async function loadLookups() {
  const [
    citiesRes,
    orgUnitsRes,
    typesRes,
    stagesRes,
    contoursRes,
    controlSystemsRes,
    contractorsRes,
  ] = await Promise.all([
    apiClient.get("/cities", { params: { limit: 500 } }),
    apiClient.get("/org-units", { params: { limit: 500 } }),
    apiClient.get("/project-types", { params: { limit: 500 } }),
    apiClient.get("/project-stages", { params: { limit: 500 } }),
    apiClient.get("/contours", { params: { limit: 500 } }),
    apiClient.get("/control-systems", { params: { limit: 500 } }),
    apiClient.get("/contractors", { params: { limit: 500 } }),
  ]);
  cities.value = citiesRes.data.items;
  orgUnits.value = orgUnitsRes.data.items;
  projectTypes.value = typesRes.data.items;
  projectStages.value = stagesRes.data.items;
  contours.value = contoursRes.data.items;
  controlSystems.value = controlSystemsRes.data.items;
  contractors.value = contractorsRes.data.items;
}

async function loadHistory() {
  const { data } = await apiClient.get(`/projects/${projectId}/history`, {
    params: { skip: historySkip.value, limit: historyLimit.value },
  });
  historyItems.value = data.items;
  historyTotal.value = data.total;
}

async function save() {
  saveError.value = "";
  saving.value = true;
  try {
    const { data } = await apiClient.patch(`/projects/${projectId}`, form);
    project.value = data;
  } catch (e) {
    saveError.value = e.response?.data?.detail || "Ошибка сохранения";
  } finally {
    saving.value = false;
  }
}

function selectTab(tab) {
  activeTab.value = tab;
  if (tab === "history" && historyItems.value.length === 0) loadHistory();
}

function goBack() {
  router.push("/projects");
}

function openGisLink() {
  if (!form.GisLink) return;
  window.open(form.GisLink, "_blank", "noopener");
}

onMounted(async () => {
  await Promise.all([loadProject(), loadLookups()]);
});
</script>

<template>
  <div v-if="project" class="profile">
    <div class="header">
      <button class="back-btn" @click="goBack">← К списку проектов</button>
      <h2>{{ project.Name }}</h2>
      <span
        class="status-badge"
        :style="{ background: PROJECT_STATUS[project.Status]?.color || '#94a3b8' }"
      >
        {{ PROJECT_STATUS[project.Status]?.label || project.Status }}
      </span>
    </div>

    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'main' }]" @click="selectTab('main')">Основное</button>
      <button :class="['tab-btn', { active: activeTab === 'history' }]" @click="selectTab('history')">История</button>
    </div>

    <section v-if="activeTab === 'main'" class="card">
      <fieldset class="section">
        <legend>Основные данные</legend>
        <div class="form-grid">
          <label class="field wide">
            Наименование
            <input v-model="form.Name" type="text" />
          </label>
          <label class="field">
            Город
            <CreatableSelect
              v-model="form.CityId"
              :options="cityOptions"
              create-endpoint="/cities"
              @created="(opt) => cities.push({ Id: opt.value, Name: opt.label })"
              @deleted="(id) => (cities = cities.filter((c) => c.Id !== id))"
            />
          </label>
          <label class="field">
            Адрес
            <input v-model="form.Address" type="text" />
          </label>
          <label class="field wide">
            Описание
            <input v-model="form.Description" type="text" />
          </label>
          <label class="field">
            Управление
            <select v-model="form.OrgUnitId">
              <option :value="null">—</option>
              <option v-for="o in orgUnitOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
            </select>
          </label>
        </div>
      </fieldset>

      <fieldset class="section">
        <legend>Проектные данные</legend>
        <div class="form-grid">
          <label class="field">
            Тип проекта
            <CreatableSelect
              v-model="form.ProjectTypeId"
              :options="projectTypeOptions"
              create-endpoint="/project-types"
              @created="(opt) => projectTypes.push({ Id: opt.value, Name: opt.label })"
              @deleted="(id) => (projectTypes = projectTypes.filter((t) => t.Id !== id))"
            />
          </label>
          <label class="field">
            Стадия проекта
            <CreatableSelect
              v-model="form.ProjectStageId"
              :options="projectStageOptions"
              create-endpoint="/project-stages"
              @created="(opt) => projectStages.push({ Id: opt.value, Name: opt.label })"
              @deleted="(id) => (projectStages = projectStages.filter((s) => s.Id !== id))"
            />
          </label>
          <label class="field">
            Контур
            <CreatableSelect
              v-model="form.ContourId"
              :options="contourOptions"
              create-endpoint="/contours"
              @created="(opt) => contours.push({ Id: opt.value, Name: opt.label })"
              @deleted="(id) => (contours = contours.filter((c) => c.Id !== id))"
            />
          </label>
          <label class="field">
            Система контроля
            <CreatableSelect
              v-model="form.ControlSystemId"
              :options="controlSystemOptions"
              create-endpoint="/control-systems"
              @created="(opt) => controlSystems.push({ Id: opt.value, Name: opt.label })"
              @deleted="(id) => (controlSystems = controlSystems.filter((s) => s.Id !== id))"
            />
          </label>
          <label class="field">
            Статус
            <select v-model="form.Status">
              <option v-for="o in statusOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
            </select>
          </label>
        </div>
      </fieldset>

      <fieldset class="section">
        <legend>Подрядчики</legend>
        <div class="form-grid">
          <label class="field">
            Застройщик
            <CreatableSelect
              v-model="form.DeveloperId"
              :options="contractorOptions"
              create-endpoint="/contractors"
              @created="(opt) => contractors.push({ Id: opt.value, Name: opt.label })"
              @deleted="(id) => (contractors = contractors.filter((c) => c.Id !== id))"
            />
          </label>
          <label class="field">
            Подрядчик
            <CreatableSelect
              v-model="form.ContractorId"
              :options="contractorOptions"
              create-endpoint="/contractors"
              @created="(opt) => contractors.push({ Id: opt.value, Name: opt.label })"
              @deleted="(id) => (contractors = contractors.filter((c) => c.Id !== id))"
            />
          </label>
          <label class="field">
            Ген подрядчик
            <CreatableSelect
              v-model="form.GeneralContractorId"
              :options="contractorOptions"
              create-endpoint="/contractors"
              @created="(opt) => contractors.push({ Id: opt.value, Name: opt.label })"
              @deleted="(id) => (contractors = contractors.filter((c) => c.Id !== id))"
            />
          </label>
          <label class="field">
            Суб подрядчик
            <CreatableSelect
              v-model="form.SubcontractorId"
              :options="contractorOptions"
              create-endpoint="/contractors"
              @created="(opt) => contractors.push({ Id: opt.value, Name: opt.label })"
              @deleted="(id) => (contractors = contractors.filter((c) => c.Id !== id))"
            />
          </label>
        </div>
      </fieldset>

      <fieldset class="section">
        <legend>Договор и характеристики</legend>
        <div class="form-grid">
          <label class="field">
            № договора
            <input v-model="form.ContractNumber" type="text" />
          </label>
          <label class="field">
            Площадь объекта
            <input v-model.number="form.Area" type="number" step="0.01" />
          </label>
          <label class="field">
            Стоимость договора
            <input v-model.number="form.Cost" type="number" step="0.01" />
          </label>
          <label class="field gis-field">
            2GIS (ссылка)
            <span class="gis-input-row">
              <input v-model="form.GisLink" type="text" />
              <button
                type="button"
                class="gis-btn"
                :disabled="!form.GisLink"
                title="Открыть в 2GIS"
                @click="openGisLink"
              >
                Открыть в 2GIS
              </button>
            </span>
          </label>
        </div>
      </fieldset>

      <fieldset class="section">
        <legend>Файлы (документы)</legend>
        <ProjectDocumentsTab :project-id="projectId" />
      </fieldset>

      <fieldset class="section">
        <legend>Даты и ГАСК</legend>
        <div class="form-grid">
          <label class="field">
            Номер талона ГАСК
            <input v-model="form.GaskTicketNumber" type="text" />
          </label>
          <label class="field">
            Номер уведомления ГАСК
            <input v-model="form.GaskNotificationNumber" type="text" />
          </label>
          <label class="field">
            Дата талона ГАСК
            <input v-model="form.GaskTicketDate" type="date" />
          </label>
          <label class="field">
            Срок действия талона ГАСК
            <input v-model="form.GaskTicketExpiryDate" type="date" />
          </label>
          <label class="field">
            Фактическая дата окончания
            <input v-model="form.ActualEndDate" type="date" />
          </label>
        </div>
      </fieldset>

      <label class="field wide comment-field">
        Комментарий
        <input v-model="form.Comment" type="text" />
      </label>

      <p v-if="saveError" class="error">{{ saveError }}</p>
      <button class="primary-btn" :disabled="saving" @click="save">
        {{ saving ? "Сохранение..." : "Сохранить" }}
      </button>
    </section>

    <section v-else-if="activeTab === 'history'" class="card">
      <table class="grid">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Кто</th>
            <th>Действие</th>
            <th>Поле</th>
            <th>Было</th>
            <th>Стало</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="h in historyItems" :key="h.Id">
            <td>{{ new Date(h.ChangedDate).toLocaleString("ru-RU") }}</td>
            <td>{{ h.ChangedByLogin || "—" }}</td>
            <td>{{ h.Action }}</td>
            <td>{{ h.FieldName || "—" }}</td>
            <td>{{ h.OldValue ?? "—" }}</td>
            <td>{{ h.NewValue ?? "—" }}</td>
          </tr>
          <tr v-if="historyItems.length === 0">
            <td colspan="6" class="empty">История пуста</td>
          </tr>
        </tbody>
      </table>
      <div class="pager">
        <button :disabled="historySkip === 0" @click="historySkip = Math.max(0, historySkip - historyLimit); loadHistory()">← Назад</button>
        <span>{{ historySkip + 1 }}–{{ Math.min(historySkip + historyLimit, historyTotal) }} из {{ historyTotal }}</span>
        <button :disabled="historySkip + historyLimit >= historyTotal" @click="historySkip += historyLimit; loadHistory()">Вперёд →</button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}
.header h2 {
  margin: 0;
}
.back-btn {
  border: none;
  background: none;
  color: #2563eb;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0;
}
.status-badge {
  padding: 0.2rem 0.7rem;
  border-radius: 999px;
  color: #fff;
  font-size: 0.8rem;
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
.section {
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  margin: 0 0 1.25rem;
  padding: 0.75rem 1rem 1rem;
  background: #eff6ff;
}
.section legend {
  padding: 0 0.4rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e40af;
}
.gis-field {
  grid-column: 1 / -1;
}
.gis-input-row {
  display: flex;
  gap: 0.5rem;
}
.gis-input-row input {
  flex: 1;
}
.gis-btn {
  flex-shrink: 0;
  padding: 0.5rem 0.9rem;
  border: 1px solid #2563eb;
  border-radius: 6px;
  background: #fff;
  color: #2563eb;
  cursor: pointer;
  font-size: 0.85rem;
  white-space: nowrap;
}
.gis-btn:disabled {
  opacity: 0.4;
  cursor: default;
  border-color: #cbd5e1;
  color: #94a3b8;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #334155;
}
.field.wide {
  grid-column: 1 / -1;
}
.field input,
.field select {
  padding: 0.5rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
}
.comment-field {
  margin-top: 0.5rem;
}
.primary-btn {
  margin-top: 1rem;
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
  margin-top: 0.75rem;
}
.grid {
  width: 100%;
  border-collapse: collapse;
}
.grid th,
.grid td {
  text-align: left;
  padding: 0.5rem 0.7rem;
  border-bottom: 1px solid #e2e8f0;
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
</style>
