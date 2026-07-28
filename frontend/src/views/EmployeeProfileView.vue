<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import apiClient from "../api/client";
import CreatableSelect from "../components/CreatableSelect.vue";
import EmployeeCertificatesTab from "../components/EmployeeCertificatesTab.vue";
import PhoneInput from "../components/PhoneInput.vue";
import { useAuthStore } from "../stores/auth";
import { EMPLOYEE_STATUS } from "../constants/employeeStatus";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const employeeId = route.params.id;

const activeTab = ref("main");
const employee = ref(null);
const form = reactive({});
const saveError = ref("");
const saving = ref(false);

const positions = ref([]);
const cities = ref([]);
const legalEntities = ref([]);

const historyItems = ref([]);
const historyTotal = ref(0);
const historySkip = ref(0);
const historyLimit = ref(20);

const FULL_PII_ROLES = ["ADMIN", "DEPARTMENT_HEAD", "GROUP_HEAD"];
const canEditPII = computed(() => FULL_PII_ROLES.includes(auth.roleCode));

const genderOptions = [
  { label: "Мужской", value: "MALE" },
  { label: "Женский", value: "FEMALE" },
];
const statusOptions = Object.entries(EMPLOYEE_STATUS).map(([value, s]) => ({
  label: s.label,
  value,
}));

const cityOptions = computed(() => cities.value.map((c) => ({ label: c.Name, value: c.Id })));
const legalEntityOptions = computed(() =>
  legalEntities.value.map((l) => ({ label: l.Name, value: l.Id })),
);
const positionOptions = computed(() =>
  positions.value.map((p) => ({ label: p.Name, value: p.Id })),
);

async function loadEmployee() {
  const { data } = await apiClient.get(`/employees/${employeeId}`);
  employee.value = data;
  Object.assign(form, {
    FullName: data.FullName,
    IIN: data.IIN,
    Email: data.Email,
    CorporatePhone: data.CorporatePhone,
    PersonalPhone: data.PersonalPhone,
    CityId: data.CityId,
    BirthDate: data.BirthDate,
    Gender: data.Gender,
    LegalEntityId: data.LegalEntityId,
    PositionId: data.PositionId,
    HireDate: data.HireDate,
    DismissalDate: data.DismissalDate,
    Status: data.Status,
    Comment: data.Comment,
  });
}

async function loadLookups() {
  const [positionsRes, citiesRes, legalEntitiesRes] = await Promise.all([
    apiClient.get("/positions", { params: { limit: 500 } }),
    apiClient.get("/cities", { params: { limit: 500 } }),
    apiClient.get("/legal-entities", { params: { limit: 500 } }),
  ]);
  positions.value = positionsRes.data.items;
  cities.value = citiesRes.data.items;
  legalEntities.value = legalEntitiesRes.data.items;
}

async function loadHistory() {
  const { data } = await apiClient.get(`/employees/${employeeId}/history`, {
    params: { skip: historySkip.value, limit: historyLimit.value },
  });
  historyItems.value = data.items;
  historyTotal.value = data.total;
}

async function save() {
  saveError.value = "";
  saving.value = true;
  try {
    const { data } = await apiClient.patch(`/employees/${employeeId}`, form);
    employee.value = data;
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
  router.push("/employees");
}

onMounted(async () => {
  await Promise.all([loadEmployee(), loadLookups()]);
});
</script>

<template>
  <div v-if="employee" class="profile">
    <div class="header">
      <button class="back-btn" @click="goBack">← К списку сотрудников</button>
      <h2>{{ employee.FullName }}</h2>
      <span
        class="status-badge"
        :style="{ background: EMPLOYEE_STATUS[employee.Status]?.color || '#94a3b8' }"
      >
        {{ EMPLOYEE_STATUS[employee.Status]?.label || employee.Status }}
      </span>
    </div>

    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'main' }]" @click="selectTab('main')">Основное</button>
      <button :class="['tab-btn', { active: activeTab === 'certs' }]" @click="selectTab('certs')">Аттестаты</button>
      <button :class="['tab-btn', { active: activeTab === 'history' }]" @click="selectTab('history')">История</button>
    </div>

    <section v-if="activeTab === 'main'" class="card">
      <div class="form-grid">
        <label class="field">
          ФИО
          <input v-model="form.FullName" type="text" />
        </label>
        <label class="field">
          ИИН
          <input v-if="canEditPII" v-model="form.IIN" type="text" maxlength="12" />
          <span v-else class="readonly-value">{{ employee.IIN || "—" }}</span>
        </label>
        <label class="field">
          Email
          <input v-model="form.Email" type="text" />
        </label>
        <label class="field">
          Корпоративный телефон
          <PhoneInput v-model="form.CorporatePhone" />
        </label>
        <label class="field">
          Личный телефон
          <PhoneInput v-if="canEditPII" v-model="form.PersonalPhone" />
          <span v-else class="readonly-value">{{ employee.PersonalPhone || "—" }}</span>
        </label>
        <label class="field">
          Дата рождения
          <input v-model="form.BirthDate" type="date" />
        </label>
        <label class="field">
          Пол
          <select v-model="form.Gender">
            <option value="" disabled>Выберите...</option>
            <option v-for="o in genderOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </label>
        <label class="field">
          Город
          <CreatableSelect
            v-model="form.CityId"
            :options="cityOptions"
            create-endpoint="/cities"
            @created="(opt) => cities.push({ Id: opt.value, Name: opt.label })"
          />
        </label>
        <label class="field">
          ТОО
          <CreatableSelect
            v-model="form.LegalEntityId"
            :options="legalEntityOptions"
            create-endpoint="/legal-entities"
            @created="(opt) => legalEntities.push({ Id: opt.value, Name: opt.label })"
          />
        </label>
        <label class="field">
          Должность
          <CreatableSelect
            v-model="form.PositionId"
            :options="positionOptions"
            create-endpoint="/positions"
            @created="(opt) => positions.push({ Id: opt.value, Name: opt.label })"
          />
        </label>
        <label class="field">
          Дата приёма
          <input v-model="form.HireDate" type="date" />
        </label>
        <label class="field">
          Дата увольнения
          <input v-model="form.DismissalDate" type="date" />
        </label>
        <label class="field">
          Статус
          <select v-model="form.Status">
            <option v-for="o in statusOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </label>
        <label class="field wide">
          Комментарий (основание смены статуса и т.п.)
          <input v-model="form.Comment" type="text" />
        </label>
      </div>

      <p v-if="employee.CorporateTenure" class="tenure">
        Корпоративный стаж: {{ employee.CorporateTenure.Years }} г.
        {{ employee.CorporateTenure.Months }} мес.
      </p>

      <p v-if="saveError" class="error">{{ saveError }}</p>
      <button class="primary-btn" :disabled="saving" @click="save">
        {{ saving ? "Сохранение..." : "Сохранить" }}
      </button>
    </section>

    <section v-else-if="activeTab === 'certs'" class="card">
      <EmployeeCertificatesTab :employee-id="employeeId" />
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
.readonly-value {
  padding: 0.5rem 0;
  color: #64748b;
}
.tenure {
  margin-top: 1rem;
  color: #475569;
  font-size: 0.9rem;
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
