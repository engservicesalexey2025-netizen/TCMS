<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import apiClient from "../api/client";
import AdditionalWorkloadTab from "../components/AdditionalWorkloadTab.vue";
import { useAuthStore } from "../stores/auth";
import { OBJECT_CATEGORIES, SUPERVISION_STAGES } from "../constants/kpi";

const auth = useAuthStore();
const canEditMatrix = computed(() => auth.can("KPI", "UPDATE"));
const canEditSettings = computed(() => auth.can("KPI_SETTINGS", "UPDATE"));

const pageTab = ref("kpi");

const cells = ref([]);
const loading = ref(true);
const settings = reactive({});
const settingsId = ref(null);
const settingsSaving = ref(false);
const settingsError = ref("");
const settingsSaved = ref(false);

function cellFor(metricType, stage, category) {
  return cells.value.find(
    (c) => c.MetricType === metricType && c.Stage === stage && c.ObjectCategory === category,
  );
}

async function loadMatrix() {
  const { data } = await apiClient.get("/kpi/norm-matrix");
  cells.value = data;
}

async function loadSettings() {
  const { data } = await apiClient.get("/kpi/settings");
  settingsId.value = data.Id;
  Object.assign(settings, {
    WeightKpi: data.WeightKpi,
    WeightIqc: data.WeightIqc,
    WeightCri: data.WeightCri,
    WeightS1: data.WeightS1,
    WeightS2: data.WeightS2,
    WeightS3: data.WeightS3,
    WeightS4: data.WeightS4,
    WeightDiversity: data.WeightDiversity,
    WeightNormative: data.WeightNormative,
    WeightTechnical: data.WeightTechnical,
    CriTarget: data.CriTarget,
    CategoryExcellentMin: data.CategoryExcellentMin,
    CategoryGoodMin: data.CategoryGoodMin,
    CategorySatisfactoryMin: data.CategorySatisfactoryMin,
  });
}

async function saveCell(cell) {
  await apiClient.patch(`/kpi/norm-matrix/${cell.Id}`, { NormValue: cell.NormValue });
}

async function saveSettings() {
  settingsError.value = "";
  settingsSaved.value = false;
  settingsSaving.value = true;
  try {
    await apiClient.patch("/kpi/settings", settings);
    settingsSaved.value = true;
  } catch (e) {
    settingsError.value = e.response?.data?.detail || "Ошибка сохранения";
  } finally {
    settingsSaving.value = false;
  }
}

const totalWeightSum = computed(
  () => (Number(settings.WeightKpi) || 0) + (Number(settings.WeightIqc) || 0) + (Number(settings.WeightCri) || 0),
);
const kpiWeightSum = computed(
  () =>
    (Number(settings.WeightS1) || 0) +
    (Number(settings.WeightS2) || 0) +
    (Number(settings.WeightS3) || 0) +
    (Number(settings.WeightS4) || 0),
);
const iqcWeightSum = computed(
  () =>
    (Number(settings.WeightDiversity) || 0) +
    (Number(settings.WeightNormative) || 0) +
    (Number(settings.WeightTechnical) || 0),
);

onMounted(async () => {
  loading.value = true;
  await Promise.all([loadMatrix(), loadSettings()]);
  loading.value = false;
});
</script>

<template>
  <div class="kpi-view">
    <h2>KPI</h2>

    <div class="page-tabs">
      <button :class="['page-tab-btn', { active: pageTab === 'kpi' }]" @click="pageTab = 'kpi'">
        KPI
      </button>
      <button
        :class="['page-tab-btn', { active: pageTab === 'workload' }]"
        @click="pageTab = 'workload'"
      >
        Дополнительные нагрузки
      </button>
    </div>

    <template v-if="pageTab === 'workload'">
      <AdditionalWorkloadTab />
    </template>

    <template v-else>
      <p class="intro">
        Норма предписаний и инспекций по паре «тип объекта × стадия» (используются в компонентах
        S1 и S3), а также веса и целевые значения формулы ИТОГ = 0,50 × KPI + 0,35 × IQC + 0,15 × CRI-балл.
      </p>

      <template v-if="!loading">
      <section class="card">
        <h3>Норма предписаний (компонент S1)</h3>
        <div class="table-scroll">
          <table class="matrix">
            <thead>
              <tr>
                <th>Стадия \ Тип объекта</th>
                <th v-for="cat in OBJECT_CATEGORIES" :key="cat.value">{{ cat.label }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="stage in SUPERVISION_STAGES" :key="stage.value">
                <td class="stage-label">{{ stage.label }}</td>
                <td v-for="cat in OBJECT_CATEGORIES" :key="cat.value">
                  <input
                    v-if="cellFor('PRESCRIPTIONS', stage.value, cat.value)"
                    v-model.number="cellFor('PRESCRIPTIONS', stage.value, cat.value).NormValue"
                    type="number"
                    min="0"
                    class="cell-input"
                    :disabled="!canEditMatrix"
                    @change="saveCell(cellFor('PRESCRIPTIONS', stage.value, cat.value))"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="card">
        <h3>Норма инспекций (компонент S3)</h3>
        <div class="table-scroll">
          <table class="matrix">
            <thead>
              <tr>
                <th>Стадия \ Тип объекта</th>
                <th v-for="cat in OBJECT_CATEGORIES" :key="cat.value">{{ cat.label }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="stage in SUPERVISION_STAGES" :key="stage.value">
                <td class="stage-label">{{ stage.label }}</td>
                <td v-for="cat in OBJECT_CATEGORIES" :key="cat.value">
                  <input
                    v-if="cellFor('INSPECTIONS', stage.value, cat.value)"
                    v-model.number="cellFor('INSPECTIONS', stage.value, cat.value).NormValue"
                    type="number"
                    min="0"
                    class="cell-input"
                    :disabled="!canEditMatrix"
                    @change="saveCell(cellFor('INSPECTIONS', stage.value, cat.value))"
                  />
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="card">
        <h3>Веса и коэффициенты формулы ИТОГ</h3>

        <fieldset class="section">
          <legend>Веса блоков (ИТОГ = WeightKpi×KPI + WeightIqc×IQC + WeightCri×CRI-балл)</legend>
          <div class="form-grid">
            <label class="field">
              KPI
              <input v-model.number="settings.WeightKpi" type="number" step="0.01" :disabled="!canEditSettings" />
            </label>
            <label class="field">
              IQC
              <input v-model.number="settings.WeightIqc" type="number" step="0.01" :disabled="!canEditSettings" />
            </label>
            <label class="field">
              CRI
              <input v-model.number="settings.WeightCri" type="number" step="0.01" :disabled="!canEditSettings" />
            </label>
          </div>
          <p class="hint" :class="{ warn: Math.abs(totalWeightSum - 1) > 0.001 }">
            Сумма весов: {{ totalWeightSum.toFixed(4) }} (должна быть 1,0000)
          </p>
        </fieldset>

        <fieldset class="section">
          <legend>Веса компонентов KPI (S1 — норма предписаний, S2 — дисциплина, S3 — норма инспекций, S4 — равномерность)</legend>
          <div class="form-grid">
            <label class="field">
              S1
              <input v-model.number="settings.WeightS1" type="number" step="0.01" :disabled="!canEditSettings" />
            </label>
            <label class="field">
              S2
              <input v-model.number="settings.WeightS2" type="number" step="0.01" :disabled="!canEditSettings" />
            </label>
            <label class="field">
              S3
              <input v-model.number="settings.WeightS3" type="number" step="0.01" :disabled="!canEditSettings" />
            </label>
            <label class="field">
              S4
              <input v-model.number="settings.WeightS4" type="number" step="0.01" :disabled="!canEditSettings" />
            </label>
          </div>
          <p class="hint" :class="{ warn: Math.abs(kpiWeightSum - 1) > 0.001 }">
            Сумма весов: {{ kpiWeightSum.toFixed(4) }} (должна быть 1,0000)
          </p>
        </fieldset>

        <fieldset class="section">
          <legend>Веса компонентов IQC (охват видов работ, доля со ссылкой на норматив, инженерная глубина текста)</legend>
          <div class="form-grid">
            <label class="field">
              Diversity
              <input v-model.number="settings.WeightDiversity" type="number" step="0.0001" :disabled="!canEditSettings" />
            </label>
            <label class="field">
              Normative
              <input v-model.number="settings.WeightNormative" type="number" step="0.0001" :disabled="!canEditSettings" />
            </label>
            <label class="field">
              Technical
              <input v-model.number="settings.WeightTechnical" type="number" step="0.0001" :disabled="!canEditSettings" />
            </label>
          </div>
          <p class="hint" :class="{ warn: Math.abs(iqcWeightSum - 1) > 0.001 }">
            Сумма весов: {{ iqcWeightSum.toFixed(4) }} (должна быть 1,0000)
          </p>
        </fieldset>

        <fieldset class="section">
          <legend>Целевое значение CRI (CRI-балл = МИН(CRI ÷ CriTarget; 1) × 100)</legend>
          <div class="form-grid">
            <label class="field">
              CRI-цель
              <input v-model.number="settings.CriTarget" type="number" step="0.01" :disabled="!canEditSettings" />
            </label>
          </div>
        </fieldset>

        <fieldset class="section">
          <legend>Границы категорий по итоговому баллу (нижняя граница каждой категории)</legend>
          <div class="form-grid">
            <label class="field">
              Отлично, от
              <input v-model.number="settings.CategoryExcellentMin" type="number" step="0.1" :disabled="!canEditSettings" />
            </label>
            <label class="field">
              Хорошо, от
              <input v-model.number="settings.CategoryGoodMin" type="number" step="0.1" :disabled="!canEditSettings" />
            </label>
            <label class="field">
              Удовлетворительно, от
              <input v-model.number="settings.CategorySatisfactoryMin" type="number" step="0.1" :disabled="!canEditSettings" />
            </label>
          </div>
        </fieldset>

        <p v-if="settingsError" class="error">{{ settingsError }}</p>
        <p v-if="settingsSaved" class="saved-hint">Сохранено</p>
        <button v-if="canEditSettings" class="primary-btn" :disabled="settingsSaving" @click="saveSettings">
          {{ settingsSaving ? "Сохранение..." : "Сохранить" }}
        </button>
      </section>
      </template>
    </template>
  </div>
</template>

<style scoped>
.kpi-view h2 {
  margin: 0 0 0.5rem;
}
.page-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}
.page-tab-btn {
  border: 1px solid #cbd5e1;
  background: #fff;
  padding: 0.4rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  color: #334155;
}
.page-tab-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}
.intro {
  color: #64748b;
  font-size: 0.9rem;
  max-width: 60rem;
  margin: 0 0 1.25rem;
}
.card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.5rem;
  margin-bottom: 1.25rem;
}
.card h3 {
  margin: 0 0 1rem;
}
.table-scroll {
  overflow-x: auto;
}
.matrix {
  width: 100%;
  border-collapse: collapse;
}
.matrix th,
.matrix td {
  border: 1px solid #e2e8f0;
  padding: 0.4rem 0.6rem;
  text-align: center;
  font-size: 0.85rem;
  white-space: nowrap;
}
.matrix th {
  background: #f8fafc;
  color: #334155;
}
.stage-label {
  text-align: left !important;
  color: #334155;
  font-weight: 500;
}
.cell-input {
  width: 4.5rem;
  padding: 0.3rem 0.4rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  text-align: center;
  font-size: 0.85rem;
}
.section {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin: 0 0 1.25rem;
  padding: 0.75rem 1rem 1rem;
}
.section legend {
  padding: 0 0.4rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #334155;
  max-width: 100%;
  white-space: normal;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
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
  font-size: 0.9rem;
}
.hint {
  margin: 0.5rem 0 0;
  font-size: 0.8rem;
  color: #64748b;
}
.hint.warn {
  color: #dc2626;
  font-weight: 500;
}
.primary-btn {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
}
.primary-btn:disabled {
  opacity: 0.5;
  cursor: default;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
  margin: 0.75rem 0;
}
.saved-hint {
  color: #16a34a;
  font-size: 0.85rem;
  margin: 0.75rem 0;
}
</style>
