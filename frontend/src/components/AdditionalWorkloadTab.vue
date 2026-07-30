<script setup>
import { computed, onMounted, ref } from "vue";
import apiClient from "../api/client";
import { useAuthStore } from "../stores/auth";
import { WORKLOAD_CATEGORIES } from "../constants/workloadNorms";

const auth = useAuthStore();
const canWrite = computed(() => auth.can("WORKLOAD_NORMS", "UPDATE"));

const rows = ref([]);
const loading = ref(true);

function rowFor(category) {
  return rows.value.find((r) => r.Category === category);
}

async function load() {
  const { data } = await apiClient.get("/workload-norms");
  rows.value = data;
}

async function saveRow(row) {
  await apiClient.patch(`/workload-norms/${row.Id}`, {
    NormValue: row.NormValue,
    SignalValue: row.SignalValue,
    LimitValue: row.LimitValue,
    Coefficient: row.Coefficient,
    MetricLinkUrl: row.MetricLinkUrl,
  });
}

onMounted(async () => {
  loading.value = true;
  await load();
  loading.value = false;
});
</script>

<template>
  <div class="workload-tab">
    <p class="intro">
      Нормы дополнительной нагрузки по направлениям (регламент BIG-HRM-RGL-038-RU) — используются
      при расчёте ежеквартальной надбавки за объёмы работ сверх нормы. Для направлений «Инженер ТН»
      задан явный коэффициент надбавки; для руководителей групп/управлений расчёт по регламенту
      ведётся по внешней метрике (ссылка) — коэффициент не указан.
    </p>

    <div v-if="!loading" class="table-scroll">
      <table class="grid">
        <thead>
          <tr>
            <th>Категория</th>
            <th>Норма, м²</th>
            <th>Сигнал к привлечению помощника, м²</th>
            <th>Предел, выше которого расчёт не производится, м²</th>
            <th>Коэффициент</th>
            <th>Ссылка на расчёт метрики</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="cat in WORKLOAD_CATEGORIES" :key="cat.value">
            <td class="category-label">{{ cat.label }}</td>
            <template v-if="rowFor(cat.value)">
              <td>
                <input
                  v-model.number="rowFor(cat.value).NormValue"
                  type="number"
                  min="0"
                  class="cell-input"
                  :disabled="!canWrite"
                  @change="saveRow(rowFor(cat.value))"
                />
              </td>
              <td>
                <input
                  v-model.number="rowFor(cat.value).SignalValue"
                  type="number"
                  min="0"
                  class="cell-input"
                  :disabled="!canWrite"
                  @change="saveRow(rowFor(cat.value))"
                />
              </td>
              <td>
                <input
                  v-model.number="rowFor(cat.value).LimitValue"
                  type="number"
                  min="0"
                  class="cell-input"
                  :disabled="!canWrite"
                  @change="saveRow(rowFor(cat.value))"
                />
              </td>
              <td>
                <input
                  v-model.number="rowFor(cat.value).Coefficient"
                  type="number"
                  step="0.0001"
                  min="0"
                  class="cell-input coefficient-input"
                  :disabled="!canWrite"
                  @change="saveRow(rowFor(cat.value))"
                />
              </td>
              <td>
                <input
                  v-model="rowFor(cat.value).MetricLinkUrl"
                  type="text"
                  class="link-input"
                  placeholder="—"
                  :disabled="!canWrite"
                  @change="saveRow(rowFor(cat.value))"
                />
              </td>
            </template>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.intro {
  color: #64748b;
  font-size: 0.9rem;
  max-width: 60rem;
  margin: 0 0 1.25rem;
}
.table-scroll {
  overflow-x: auto;
}
.grid {
  width: 100%;
  border-collapse: collapse;
}
.grid th,
.grid td {
  border: 1px solid #e2e8f0;
  padding: 0.5rem 0.6rem;
  text-align: center;
  font-size: 0.85rem;
  white-space: nowrap;
}
.grid th {
  background: #f8fafc;
  color: #334155;
}
.category-label {
  text-align: left !important;
  color: #334155;
  white-space: normal;
  max-width: 18rem;
}
.cell-input {
  width: 6.5rem;
  padding: 0.35rem 0.4rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  text-align: center;
  font-size: 0.85rem;
}
.coefficient-input {
  width: 5rem;
}
.link-input {
  width: 16rem;
  padding: 0.35rem 0.4rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.8rem;
}
</style>
