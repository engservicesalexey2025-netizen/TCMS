<script setup>
import { computed, ref } from "vue";
import { useRoute } from "vue-router";
import apiClient from "../api/client";

const route = useRoute();
const entityType = route.params.entityType;

const stage = ref("upload"); // upload | review | done
const uploading = ref(false);
const uploadError = ref("");

const session = ref(null);
const rows = ref([]);
const rowsTotal = ref(0);
const rowsSkip = ref(0);
const rowsLimit = ref(20);
const activeTab = ref("ALL");
const expandedRowId = ref(null);
const applying = ref(false);
const applyResult = ref(null);
const applyError = ref("");
const failedRows = ref([]);

const CLASSIFICATION_LABELS = {
  NEW: "Новое",
  IDENTICAL: "Совпало",
  CONFLICT: "Расхождение",
  AMBIGUOUS: "Неоднозначно",
  ERROR: "Ошибка",
};
const TABS = ["ALL", "NEW", "CONFLICT", "IDENTICAL", "AMBIGUOUS", "ERROR"];
const CONFIRMABLE = new Set(["NEW", "IDENTICAL", "CONFLICT"]);

const counts = computed(() => session.value?.Counts || {});

async function downloadTemplate() {
  const response = await apiClient.get(`/imports/${entityType}/template`, {
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = `${entityType}_template.xlsx`;
  link.click();
  window.URL.revokeObjectURL(url);
}

async function handleFileChange(event) {
  const file = event.target.files[0];
  if (!file) return;
  uploading.value = true;
  uploadError.value = "";
  try {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await apiClient.post(`/imports/${entityType}/sessions`, formData);
    session.value = data;
    if (data.Status === "FAILED") {
      uploadError.value = data.ErrorMessage || "Не удалось обработать файл";
    } else {
      stage.value = "review";
      await loadRows();
    }
  } catch (e) {
    uploadError.value = e.response?.data?.detail || "Ошибка загрузки файла";
  } finally {
    uploading.value = false;
    event.target.value = "";
  }
}

async function loadRows() {
  const params = { skip: rowsSkip.value, limit: rowsLimit.value };
  if (activeTab.value !== "ALL") params.classification = activeTab.value;
  const { data } = await apiClient.get(`/imports/sessions/${session.value.Id}/rows`, { params });
  rows.value = data.items;
  rowsTotal.value = data.total;
}

function selectTab(tab) {
  activeTab.value = tab;
  rowsSkip.value = 0;
  loadRows();
}

async function refreshSessionAndRows() {
  const { data } = await apiClient.get(`/imports/sessions/${session.value.Id}`);
  session.value = data;
  await loadRows();
}

async function decideRow(row, decision) {
  await apiClient.patch(`/imports/sessions/${session.value.Id}/rows/${row.Id}/decision`, {
    decision,
  });
  await refreshSessionAndRows();
}

async function bulkDecide(decision) {
  await apiClient.post(`/imports/sessions/${session.value.Id}/rows/bulk-decision`, {
    decision,
    classification: activeTab.value === "ALL" ? undefined : activeTab.value,
  });
  await refreshSessionAndRows();
}

function toggleExpand(row) {
  expandedRowId.value = expandedRowId.value === row.Id ? null : row.Id;
}

async function applyImport() {
  applying.value = true;
  applyError.value = "";
  try {
    const { data } = await apiClient.post(`/imports/sessions/${session.value.Id}/apply`);
    applyResult.value = data;
    if (data.failed > 0) {
      const { data: failedPage } = await apiClient.get(
        `/imports/sessions/${session.value.Id}/rows`,
        { params: { limit: 100 } },
      );
      failedRows.value = failedPage.items.filter((r) => r.AppliedAction === "FAILED");
    }
    stage.value = "done";
  } catch (e) {
    applyError.value = e.response?.data?.detail || "Ошибка применения";
  } finally {
    applying.value = false;
  }
}
</script>

<template>
  <div class="import-view">
    <h2>Импорт: {{ entityType }}</h2>

    <section v-if="stage === 'upload'" class="card">
      <p>Загрузите файл .xlsx. Заголовки колонок должны соответствовать шаблону.</p>
      <div class="upload-actions">
        <button class="secondary-btn" @click="downloadTemplate">Скачать шаблон</button>
        <label class="file-btn">
          {{ uploading ? "Загрузка..." : "Выбрать файл" }}
          <input type="file" accept=".xlsx" :disabled="uploading" @change="handleFileChange" hidden />
        </label>
      </div>
      <p v-if="uploadError" class="error">{{ uploadError }}</p>
    </section>

    <section v-else-if="stage === 'review'" class="card">
      <div class="counts">
        <span v-for="(label, key) in CLASSIFICATION_LABELS" :key="key" class="count-badge">
          {{ label }}: {{ counts[key] || 0 }}
        </span>
      </div>

      <div class="tabs">
        <button
          v-for="tab in TABS"
          :key="tab"
          :class="['tab-btn', { active: activeTab === tab }]"
          @click="selectTab(tab)"
        >
          {{ tab === "ALL" ? "Все" : CLASSIFICATION_LABELS[tab] }}
        </button>
        <div class="spacer" />
        <button
          v-if="activeTab === 'ALL' || CONFIRMABLE.has(activeTab)"
          class="secondary-btn"
          @click="bulkDecide('CONFIRMED')"
        >
          Подтвердить все ({{ activeTab === "ALL" ? "кроме неподтверждаемых" : CLASSIFICATION_LABELS[activeTab] }})
        </button>
        <button class="secondary-btn" @click="bulkDecide('REJECTED')">Отклонить все</button>
      </div>

      <table class="grid">
        <thead>
          <tr>
            <th>#</th>
            <th v-for="col in session.Columns" :key="col.field">{{ col.header }}</th>
            <th>Классификация</th>
            <th>Решение</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="row in rows" :key="row.Id">
            <tr :class="`row-${row.Classification.toLowerCase()}`">
              <td>{{ row.RowNumber }}</td>
              <td v-for="col in session.Columns" :key="col.field">{{ row.RawData[col.field] }}</td>
              <td>{{ CLASSIFICATION_LABELS[row.Classification] }}</td>
              <td>{{ row.Decision }}</td>
              <td class="actions">
                <button class="link-btn" @click="toggleExpand(row)">Детали</button>
                <button
                  v-if="CONFIRMABLE.has(row.Classification)"
                  class="link-btn"
                  @click="decideRow(row, 'CONFIRMED')"
                >
                  Подтвердить
                </button>
                <button class="link-btn" @click="decideRow(row, 'REJECTED')">Отклонить</button>
              </td>
            </tr>
            <tr v-if="expandedRowId === row.Id" class="detail-row">
              <td :colspan="session.Columns.length + 4">
                <div v-if="row.ValidationError" class="detail-error">
                  Ошибка: {{ row.ValidationError }}
                </div>
                <div v-else-if="row.Classification === 'AMBIGUOUS'" class="detail-error">
                  Найдено несколько совпадающих записей — требуется ручное разрешение.
                </div>
                <table v-else-if="row.DiffFields" class="diff-table">
                  <thead>
                    <tr><th>Поле</th><th>Было</th><th>Станет</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(change, field) in row.DiffFields" :key="field">
                      <td>{{ field }}</td>
                      <td>{{ change.old ?? "—" }}</td>
                      <td>{{ change.new ?? "—" }}</td>
                    </tr>
                  </tbody>
                </table>
                <div v-else>Новая запись, будет создана как есть.</div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>

      <div class="pager">
        <button :disabled="rowsSkip === 0" @click="rowsSkip = Math.max(0, rowsSkip - rowsLimit); loadRows()">← Назад</button>
        <span>{{ rowsSkip + 1 }}–{{ Math.min(rowsSkip + rowsLimit, rowsTotal) }} из {{ rowsTotal }}</span>
        <button :disabled="rowsSkip + rowsLimit >= rowsTotal" @click="rowsSkip += rowsLimit; loadRows()">Вперёд →</button>
      </div>

      <div class="apply-bar">
        <p v-if="applyError" class="error">{{ applyError }}</p>
        <button class="primary-btn" :disabled="applying" @click="applyImport">
          {{ applying ? "Применение..." : "Применить" }}
        </button>
      </div>
    </section>

    <section v-else-if="stage === 'done'" class="card">
      <h3>Импорт применён</h3>
      <ul class="result-list">
        <li>Создано: {{ applyResult.created }}</li>
        <li>Обновлено: {{ applyResult.updated }}</li>
        <li>Пропущено: {{ applyResult.skipped }}</li>
        <li>Ошибок: {{ applyResult.failed }}</li>
      </ul>
      <div v-if="failedRows.length" class="failed-rows">
        <h4>Строки с ошибками применения</h4>
        <ul>
          <li v-for="row in failedRows" :key="row.Id">
            Строка {{ row.RowNumber }}: {{ row.AppliedError }}
          </li>
        </ul>
      </div>
      <router-link to="/imports" class="secondary-btn">К истории импортов</router-link>
    </section>
  </div>
</template>

<style scoped>
.import-view {
  max-width: 100%;
}
.card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.5rem;
}
.upload-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}
.file-btn,
.secondary-btn,
.primary-btn {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
  text-decoration: none;
}
.primary-btn {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}
.counts {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: #475569;
}
.count-badge {
  background: #f1f5f9;
  padding: 0.3rem 0.7rem;
  border-radius: 999px;
}
.tabs {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.spacer {
  flex: 1;
}
.tab-btn {
  border: 1px solid #cbd5e1;
  background: #fff;
  padding: 0.35rem 0.8rem;
  border-radius: 999px;
  cursor: pointer;
  font-size: 0.85rem;
}
.tab-btn.active {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
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
.row-conflict {
  background: #fffbeb;
}
.row-error,
.row-ambiguous {
  background: #fef2f2;
}
.row-new {
  background: #f0fdf4;
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
  margin-right: 0.6rem;
  font-size: 0.8rem;
}
.detail-row td {
  background: #f8fafc;
}
.detail-error {
  color: #dc2626;
  font-size: 0.85rem;
}
.diff-table {
  width: auto;
  border-collapse: collapse;
}
.diff-table th,
.diff-table td {
  padding: 0.3rem 0.8rem;
  font-size: 0.8rem;
  border-bottom: 1px solid #e2e8f0;
}
.pager {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1rem 0;
  font-size: 0.85rem;
  color: #475569;
}
.apply-bar {
  margin-top: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
}
.result-list {
  font-size: 0.95rem;
  line-height: 1.8;
}
.failed-rows {
  margin-top: 1rem;
  color: #dc2626;
  font-size: 0.85rem;
}
</style>
