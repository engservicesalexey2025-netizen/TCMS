<script setup>
import { computed, onMounted, ref, watch } from "vue";
import apiClient from "../api/client";
import EntityTable from "../components/EntityTable.vue";
import ProjectCard from "../components/ProjectCard.vue";
import { useAuthStore } from "../stores/auth";
import { PROJECT_STATUS } from "../constants/projectStatus";

const auth = useAuthStore();
const tablePermissions = computed(() => ({
  create: auth.can("PROJECTS", "CREATE"),
  edit: auth.can("PROJECTS", "UPDATE"),
  delete: auth.can("PROJECTS", "DELETE"),
  import: auth.can("PROJECTS", "IMPORT"),
  export: auth.can("PROJECTS", "EXPORT"),
}));

const cities = ref([]);
const orgUnits = ref([]);
const projectTypes = ref([]);
const projectStages = ref([]);
const contours = ref([]);
const controlSystems = ref([]);
const contractors = ref([]);
const stats = ref({});

async function loadStats() {
  const { data } = await apiClient.get("/projects/stats");
  stats.value = data;
}

onMounted(async () => {
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
    loadStats(),
  ]);
  cities.value = citiesRes.data.items;
  orgUnits.value = orgUnitsRes.data.items;
  projectTypes.value = typesRes.data.items;
  projectStages.value = stagesRes.data.items;
  contours.value = contoursRes.data.items;
  controlSystems.value = controlSystemsRes.data.items;
  contractors.value = contractorsRes.data.items;
});

const activeQuickFilter = ref(null);

const quickFilters = computed(() => [
  { key: null, label: "Все", count: stats.value.Total ?? 0 },
  { key: "city", label: "Без города", count: stats.value.city ?? 0 },
  { key: "org_unit", label: "Без управления", count: stats.value.org_unit ?? 0 },
  { key: "project_type", label: "Без типа проекта", count: stats.value.project_type ?? 0 },
  { key: "project_stage", label: "Без стадии проекта", count: stats.value.project_stage ?? 0 },
  { key: "control_system", label: "Без системы контроля", count: stats.value.control_system ?? 0 },
  { key: "contract_number", label: "Без № договора", count: stats.value.contract_number ?? 0 },
  { key: "area", label: "Без площади", count: stats.value.area ?? 0 },
  { key: "cost", label: "Без стоимости", count: stats.value.cost ?? 0 },
  { key: "gis_link", label: "Без 2GIS", count: stats.value.gis_link ?? 0 },
  {
    key: "gask_notification_number",
    label: "Без номера уведомления ГАСК",
    count: stats.value.gask_notification_number ?? 0,
  },
]);

const quickFilterParams = computed(() =>
  activeQuickFilter.value ? { missing_field: activeQuickFilter.value } : {},
);

function selectQuickFilter(key) {
  activeQuickFilter.value = key;
  if (key) viewMode.value = "table";
}

function rowClassFn(row) {
  if (!row.GaskTicketExpiryDate) return "";
  const expiry = new Date(`${row.GaskTicketExpiryDate}T00:00:00`);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  if (expiry < today) return "row-danger";
  const oneMonthOut = new Date(today);
  oneMonthOut.setMonth(oneMonthOut.getMonth() + 1);
  if (expiry <= oneMonthOut) return "row-warning";
  return "";
}

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

function labelFor(options, id) {
  return options.find((o) => o.value === id)?.label || "";
}

const columns = computed(() => [
  { field: "Name", header: "Наименование" },
  { field: "CityId", header: "Город", options: cityOptions.value },
  { field: "Address", header: "Адрес" },
  { field: "OrgUnitId", header: "Управление", options: orgUnitOptions.value },
  { field: "ProjectTypeId", header: "Тип проекта", options: projectTypeOptions.value },
  { field: "ProjectStageId", header: "Стадия проекта", options: projectStageOptions.value },
  { field: "ContourId", header: "Контур", options: contourOptions.value },
  { field: "ControlSystemId", header: "Система контроля", options: controlSystemOptions.value },
  { field: "Status", header: "Статус", type: "badge", map: PROJECT_STATUS },
  { field: "DeveloperId", header: "Застройщик", options: contractorOptions.value },
  { field: "ContractorId", header: "Подрядчик", options: contractorOptions.value },
  { field: "GeneralContractorId", header: "Ген подрядчик", options: contractorOptions.value },
  { field: "SubcontractorId", header: "Суб подрядчик", options: contractorOptions.value },
  { field: "ContractNumber", header: "№ договора" },
  { field: "Area", header: "Площадь объекта" },
  { field: "Cost", header: "Стоимость договора" },
  { field: "GisLink", header: "2GIS (ссылка)" },
  { field: "GaskTicketNumber", header: "Номер талона ГАСК" },
  { field: "GaskNotificationNumber", header: "Номер уведомления ГАСК" },
  { field: "GaskTicketDate", header: "Дата талона ГАСК" },
  { field: "GaskTicketExpiryDate", header: "Срок действия талона ГАСК" },
  { field: "ActualEndDate", header: "Фактическая дата окончания" },
]);

const formFields = computed(() => [
  { field: "Name", label: "Наименование", type: "text" },
  {
    field: "CityId",
    label: "Город",
    type: "creatable-select",
    options: cityOptions.value,
    createEndpoint: "/cities",
    onCreated: (opt) => cities.value.push({ Id: opt.value, Name: opt.label }),
    onDeleted: (id) => (cities.value = cities.value.filter((c) => c.Id !== id)),
  },
  { field: "Address", label: "Адрес", type: "text" },
  { field: "OrgUnitId", label: "Управление", type: "select", options: orgUnitOptions.value },
  {
    field: "ProjectTypeId",
    label: "Тип проекта",
    type: "creatable-select",
    options: projectTypeOptions.value,
    createEndpoint: "/project-types",
    onCreated: (opt) => projectTypes.value.push({ Id: opt.value, Name: opt.label }),
    onDeleted: (id) => (projectTypes.value = projectTypes.value.filter((t) => t.Id !== id)),
  },
  {
    field: "ProjectStageId",
    label: "Стадия проекта",
    type: "creatable-select",
    options: projectStageOptions.value,
    createEndpoint: "/project-stages",
    onCreated: (opt) => projectStages.value.push({ Id: opt.value, Name: opt.label }),
    onDeleted: (id) => (projectStages.value = projectStages.value.filter((s) => s.Id !== id)),
  },
  {
    field: "ContourId",
    label: "Контур",
    type: "creatable-select",
    options: contourOptions.value,
    createEndpoint: "/contours",
    onCreated: (opt) => contours.value.push({ Id: opt.value, Name: opt.label }),
    onDeleted: (id) => (contours.value = contours.value.filter((c) => c.Id !== id)),
  },
  {
    field: "ControlSystemId",
    label: "Система контроля",
    type: "creatable-select",
    options: controlSystemOptions.value,
    createEndpoint: "/control-systems",
    onCreated: (opt) => controlSystems.value.push({ Id: opt.value, Name: opt.label }),
    onDeleted: (id) => (controlSystems.value = controlSystems.value.filter((s) => s.Id !== id)),
  },
  { field: "Status", label: "Статус", type: "select", options: statusOptions, default: "IN_PROGRESS" },
  {
    field: "DeveloperId",
    label: "Застройщик",
    type: "creatable-select",
    options: contractorOptions.value,
    createEndpoint: "/contractors",
    onCreated: (opt) => contractors.value.push({ Id: opt.value, Name: opt.label }),
    onDeleted: (id) => (contractors.value = contractors.value.filter((c) => c.Id !== id)),
  },
  {
    field: "ContractorId",
    label: "Подрядчик",
    type: "creatable-select",
    options: contractorOptions.value,
    createEndpoint: "/contractors",
    onCreated: (opt) => contractors.value.push({ Id: opt.value, Name: opt.label }),
    onDeleted: (id) => (contractors.value = contractors.value.filter((c) => c.Id !== id)),
  },
  {
    field: "GeneralContractorId",
    label: "Ген подрядчик",
    type: "creatable-select",
    options: contractorOptions.value,
    createEndpoint: "/contractors",
    onCreated: (opt) => contractors.value.push({ Id: opt.value, Name: opt.label }),
    onDeleted: (id) => (contractors.value = contractors.value.filter((c) => c.Id !== id)),
  },
  {
    field: "SubcontractorId",
    label: "Суб подрядчик",
    type: "creatable-select",
    options: contractorOptions.value,
    createEndpoint: "/contractors",
    onCreated: (opt) => contractors.value.push({ Id: opt.value, Name: opt.label }),
    onDeleted: (id) => (contractors.value = contractors.value.filter((c) => c.Id !== id)),
  },
  { field: "ContractNumber", label: "№ договора", type: "text" },
  { field: "Area", label: "Площадь объекта", type: "number" },
  { field: "Cost", label: "Стоимость договора", type: "number" },
  { field: "GisLink", label: "2GIS (ссылка)", type: "text" },
  { field: "GaskTicketNumber", label: "Номер талона ГАСК", type: "text" },
  { field: "GaskNotificationNumber", label: "Номер уведомления ГАСК", type: "text" },
  { field: "GaskTicketDate", label: "Дата талона ГАСК", type: "date" },
  { field: "GaskTicketExpiryDate", label: "Срок действия талона ГАСК", type: "date" },
  { field: "ActualEndDate", label: "Фактическая дата окончания", type: "date" },
]);

const viewMode = ref(localStorage.getItem("projects_view_mode") || "table");
watch(viewMode, (mode) => localStorage.setItem("projects_view_mode", mode));

const cardItems = ref([]);
const cardTotal = ref(0);
const cardSkip = ref(0);
const cardLimit = ref(24);
const cardSearch = ref("");

async function loadCards() {
  const { data } = await apiClient.get("/projects", {
    params: { skip: cardSkip.value, limit: cardLimit.value, search: cardSearch.value || undefined },
  });
  cardItems.value = data.items;
  cardTotal.value = data.total;
}

watch(
  viewMode,
  (mode) => {
    if (mode === "cards") loadCards();
  },
  { immediate: true },
);
</script>

<template>
  <div>
    <p v-if="stats.GaskExpired" class="banner banner-danger">
      Необходимо продлить Талон — просрочен срок действия талона ГАСК у {{ stats.GaskExpired }}
      проект(ов).
    </p>
    <p v-if="stats.GaskExpiringSoon" class="banner banner-warning">
      Внимание: у {{ stats.GaskExpiringSoon }} проект(ов) истекает срок действия талона ГАСК в
      течение месяца.
    </p>

    <div class="quick-filters">
      <button
        v-for="qf in quickFilters"
        :key="qf.key ?? 'all'"
        :class="['chip', { active: activeQuickFilter === qf.key }]"
        @click="selectQuickFilter(qf.key)"
      >
        {{ qf.label }} ({{ qf.count }})
      </button>
    </div>

    <div class="view-toggle">
      <button :class="{ active: viewMode === 'table' }" @click="viewMode = 'table'">Таблица</button>
      <button :class="{ active: viewMode === 'cards' }" @click="viewMode = 'cards'">Карточки</button>
    </div>

    <EntityTable
      v-if="viewMode === 'table'"
      resource="/projects"
      title="Проекты"
      :columns="columns"
      :form-fields="formFields"
      :permissions="tablePermissions"
      column-permission-module="PROJECTS"
      :extra-params="quickFilterParams"
      :row-class="rowClassFn"
      import-resource="projects"
      row-link="/projects"
      edit-link="/projects"
      export-resource
      @changed="loadStats"
    />

    <div v-else>
      <div class="cards-toolbar">
        <h2>Проекты</h2>
        <div class="spacer" />
        <input v-model="cardSearch" placeholder="Поиск..." @keyup.enter="loadCards" />
      </div>
      <div class="cards-grid">
        <ProjectCard
          v-for="p in cardItems"
          :key="p.Id"
          :project="p"
          :city-label="labelFor(cityOptions, p.CityId)"
          :org-unit-label="labelFor(orgUnitOptions, p.OrgUnitId)"
          :project-type-label="labelFor(projectTypeOptions, p.ProjectTypeId)"
        />
        <p v-if="cardItems.length === 0" class="empty">Нет записей</p>
      </div>
      <div class="pager">
        <button :disabled="cardSkip === 0" @click="cardSkip = Math.max(0, cardSkip - cardLimit); loadCards()">← Назад</button>
        <span>{{ cardSkip + 1 }}–{{ Math.min(cardSkip + cardLimit, cardTotal) }} из {{ cardTotal }}</span>
        <button :disabled="cardSkip + cardLimit >= cardTotal" @click="cardSkip += cardLimit; loadCards()">Вперёд →</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.banner {
  margin: 0 0 0.75rem;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
}
.banner-danger {
  background: #fecaca;
  color: #7f1d1d;
  border: 1px solid #fca5a5;
}
.banner-warning {
  background: #fef9c3;
  color: #713f12;
  border: 1px solid #fde047;
}
.quick-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.chip {
  border: 1px solid #cbd5e1;
  background: #fff;
  padding: 0.35rem 0.9rem;
  border-radius: 999px;
  cursor: pointer;
  font-size: 0.85rem;
  color: #334155;
  white-space: nowrap;
}
.chip:hover {
  background: #f1f5f9;
}
.chip.active {
  background: #16a34a;
  border-color: #16a34a;
  color: #fff;
}
.view-toggle {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.view-toggle button {
  border: 1px solid #cbd5e1;
  background: #fff;
  padding: 0.4rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  color: #334155;
}
.view-toggle button.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}
.cards-toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.cards-toolbar h2 {
  margin: 0;
}
.spacer {
  flex: 1;
}
.cards-toolbar input {
  padding: 0.4rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1rem;
}
.empty {
  color: #94a3b8;
  padding: 1.5rem;
}
.pager {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1rem;
  font-size: 0.85rem;
  color: #475569;
}
</style>
