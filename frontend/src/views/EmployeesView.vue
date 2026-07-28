<script setup>
import { computed, onMounted, ref, watch } from "vue";
import apiClient from "../api/client";
import EntityTable from "../components/EntityTable.vue";
import EmployeeCard from "../components/EmployeeCard.vue";
import { EMPLOYEE_STATUS } from "../constants/employeeStatus";

const positions = ref([]);
const cities = ref([]);
const legalEntities = ref([]);

onMounted(async () => {
  const [positionsRes, citiesRes, legalEntitiesRes] = await Promise.all([
    apiClient.get("/positions", { params: { limit: 500 } }),
    apiClient.get("/cities", { params: { limit: 500 } }),
    apiClient.get("/legal-entities", { params: { limit: 500 } }),
  ]);
  positions.value = positionsRes.data.items;
  cities.value = citiesRes.data.items;
  legalEntities.value = legalEntitiesRes.data.items;
});

const positionOptions = computed(() =>
  positions.value.map((p) => ({ label: p.Name, value: p.Id })),
);
const cityOptions = computed(() => cities.value.map((c) => ({ label: c.Name, value: c.Id })));
const legalEntityOptions = computed(() =>
  legalEntities.value.map((l) => ({ label: l.Name, value: l.Id })),
);
const statusOptions = Object.entries(EMPLOYEE_STATUS).map(([value, s]) => ({
  label: s.label,
  value,
}));
const genderOptions = [
  { label: "Мужской", value: "MALE" },
  { label: "Женский", value: "FEMALE" },
];

function formatTenure(tenure) {
  return tenure ? `${tenure.Years} г. ${tenure.Months} мес.` : "—";
}

const columns = computed(() => [
  { field: "FullName", header: "Сотрудник" },
  { field: "PositionId", header: "Функциональная должность", options: positionOptions.value },
  { field: "IIN", header: "ИИН" },
  { field: "Email", header: "Email" },
  { field: "CorporatePhone", header: "Корпоративный номер" },
  { field: "PersonalPhone", header: "Личный номер" },
  { field: "CityId", header: "Место работы (город)", options: cityOptions.value },
  { field: "BirthDate", header: "Дата рождения" },
  { field: "Gender", header: "Пол", options: genderOptions },
  { field: "HireDate", header: "Дата приёма" },
  { field: "CorporateTenure", header: "Корпоративный стаж", format: formatTenure },
  { field: "LegalEntityId", header: "ТОО ES/Invecon", options: legalEntityOptions.value },
  { field: "Status", header: "Статус", type: "badge", map: EMPLOYEE_STATUS },
]);

const formFields = computed(() => [
  { field: "FullName", label: "ФИО", type: "text" },
  { field: "IIN", label: "ИИН (12 цифр)", type: "text" },
  { field: "Email", label: "Email", type: "text" },
  { field: "CorporatePhone", label: "Корпоративный телефон", type: "phone" },
  { field: "PersonalPhone", label: "Личный телефон", type: "phone" },
  { field: "BirthDate", label: "Дата рождения", type: "date" },
  { field: "Gender", label: "Пол", type: "select", options: genderOptions },
  {
    field: "CityId",
    label: "Город",
    type: "creatable-select",
    options: cityOptions.value,
    createEndpoint: "/cities",
    onCreated: (opt) => cities.value.push({ Id: opt.value, Name: opt.label }),
  },
  {
    field: "LegalEntityId",
    label: "ТОО",
    type: "creatable-select",
    options: legalEntityOptions.value,
    createEndpoint: "/legal-entities",
    onCreated: (opt) => legalEntities.value.push({ Id: opt.value, Name: opt.label }),
  },
  {
    field: "PositionId",
    label: "Должность",
    type: "creatable-select",
    options: positionOptions.value,
    createEndpoint: "/positions",
    onCreated: (opt) => positions.value.push({ Id: opt.value, Name: opt.label }),
  },
  { field: "HireDate", label: "Дата приёма", type: "date" },
  { field: "Status", label: "Статус", type: "select", options: statusOptions, default: "ACTIVE" },
]);

const viewMode = ref(localStorage.getItem("employees_view_mode") || "table");
watch(viewMode, (mode) => localStorage.setItem("employees_view_mode", mode));

const cardItems = ref([]);
const cardTotal = ref(0);
const cardSkip = ref(0);
const cardLimit = ref(24);
const cardSearch = ref("");

function labelFor(options, id) {
  return options.find((o) => o.value === id)?.label || "";
}

async function loadCards() {
  const { data } = await apiClient.get("/employees", {
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
    <div class="view-toggle">
      <button :class="{ active: viewMode === 'table' }" @click="viewMode = 'table'">Таблица</button>
      <button :class="{ active: viewMode === 'cards' }" @click="viewMode = 'cards'">Карточки</button>
    </div>

    <EntityTable
      v-if="viewMode === 'table'"
      resource="/employees"
      title="Сотрудники"
      :columns="columns"
      :form-fields="formFields"
      import-resource="employees"
      row-link="/employees"
      edit-link="/employees"
      export-resource
    />

    <div v-else>
      <div class="cards-toolbar">
        <h2>Сотрудники</h2>
        <div class="spacer" />
        <input v-model="cardSearch" placeholder="Поиск..." @keyup.enter="loadCards" />
      </div>
      <div class="cards-grid">
        <EmployeeCard
          v-for="emp in cardItems"
          :key="emp.Id"
          :employee="emp"
          :position-label="labelFor(positionOptions, emp.PositionId)"
          :city-label="labelFor(cityOptions, emp.CityId)"
          :legal-entity-label="labelFor(legalEntityOptions, emp.LegalEntityId)"
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
