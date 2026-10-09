<script setup>
import { computed, onMounted, ref } from "vue";
import apiClient from "../api/client";
import { useAuthStore } from "../stores/auth";
import CreatableSelect from "./CreatableSelect.vue";
import DateInput from "./DateInput.vue";

const props = defineProps({
  employeeId: { type: String, required: true },
});

const auth = useAuthStore();
// Скачивание сканов сегодня намеренно ограничено так же строго, как запись
// (см. app/api/v1/employee_certificates.py::DownloadUser) — сканы чувствительнее
// замаскированных полей карточки.
const canWrite = computed(() => auth.can("EMPLOYEE_CERTIFICATES", "UPDATE"));

const certificates = ref([]);
const certificationLevels = ref([]);
const uploading = ref(false);
const uploadError = ref("");

const pendingFile = ref(null);
const pendingNumber = ref("");
const pendingLevelId = ref(null);
const pendingIssueDate = ref("");

const levelOptions = computed(() =>
  certificationLevels.value.map((l) => ({ label: l.Name, value: l.Id })),
);

async function load() {
  const [certsRes, levelsRes] = await Promise.all([
    apiClient.get(`/employees/${props.employeeId}/certificates`, { params: { limit: 100 } }),
    apiClient.get("/certification-levels", { params: { limit: 200 } }),
  ]);
  certificates.value = certsRes.data.items;
  certificationLevels.value = levelsRes.data.items;
}

function handleFileChange(event) {
  pendingFile.value = event.target.files[0] || null;
}

async function upload() {
  if (!pendingFile.value) return;
  uploading.value = true;
  uploadError.value = "";
  try {
    const formData = new FormData();
    formData.append("file", pendingFile.value);
    if (pendingNumber.value) formData.append("certificate_number", pendingNumber.value);
    if (pendingLevelId.value) formData.append("certification_level_id", pendingLevelId.value);
    if (pendingIssueDate.value) formData.append("issue_date", pendingIssueDate.value);
    await apiClient.post(`/employees/${props.employeeId}/certificates`, formData);
    pendingFile.value = null;
    pendingNumber.value = "";
    pendingLevelId.value = null;
    pendingIssueDate.value = "";
    await load();
  } catch (e) {
    uploadError.value = e.response?.data?.detail || "Ошибка загрузки файла";
  } finally {
    uploading.value = false;
  }
}

async function updateCert(cert) {
  await apiClient.patch(`/employees/${props.employeeId}/certificates/${cert.Id}`, {
    CertificateNumber: cert.CertificateNumber,
    CertificationLevelId: cert.CertificationLevelId,
    IssueDate: cert.IssueDate || null,
  });
}

function onLevelCreated(opt) {
  certificationLevels.value.push({ Id: opt.value, Name: opt.label });
}

function onLevelDeleted(id) {
  certificationLevels.value = certificationLevels.value.filter((l) => l.Id !== id);
}

async function download(cert) {
  const response = await apiClient.get(
    `/employees/${props.employeeId}/certificates/${cert.Id}/download`,
    { responseType: "blob" },
  );
  const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
  window.open(url, "_blank");
}

async function remove(cert) {
  if (!window.confirm(`Удалить аттестат «${cert.FileName}»? Это действие необратимо.`)) {
    return;
  }
  await apiClient.delete(`/employees/${props.employeeId}/certificates/${cert.Id}`);
  await load();
}

function formatSize(bytes) {
  return `${(bytes / 1024 / 1024).toFixed(2)} МБ`;
}

onMounted(load);
</script>

<template>
  <div>
    <div v-if="canWrite" class="upload-form">
      <label class="file-btn">
        {{ pendingFile ? pendingFile.name : "Выбрать PDF" }}
        <input type="file" accept="application/pdf" @change="handleFileChange" hidden />
      </label>
      <input v-model="pendingNumber" type="text" placeholder="Номер аттестата" class="text-input" />
      <div class="level-select">
        <CreatableSelect
          v-model="pendingLevelId"
          :options="levelOptions"
          create-endpoint="/certification-levels"
          placeholder="Уровень аттестата..."
          @created="onLevelCreated"
          @deleted="onLevelDeleted"
        />
      </div>
      <DateInput v-model="pendingIssueDate" class="date-input" title="Дата аттестата" />
      <button class="primary-btn" :disabled="!pendingFile || uploading" @click="upload">
        {{ uploading ? "Загрузка..." : "Загрузить" }}
      </button>
    </div>
    <p v-if="uploadError" class="error">{{ uploadError }}</p>

    <table class="grid">
      <thead>
        <tr>
          <th>Файл</th>
          <th>Аттестат</th>
          <th>Уровень</th>
          <th>Дата аттестата</th>
          <th>Размер</th>
          <th>Загружен</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="cert in certificates" :key="cert.Id">
          <td>{{ cert.FileName }}</td>
          <td>
            <input
              v-model="cert.CertificateNumber"
              type="text"
              class="cell-input"
              :disabled="!canWrite"
              @blur="updateCert(cert)"
            />
          </td>
          <td class="level-cell">
            <CreatableSelect
              v-model="cert.CertificationLevelId"
              :options="levelOptions"
              :disabled="!canWrite"
              create-endpoint="/certification-levels"
              @created="onLevelCreated"
          @deleted="onLevelDeleted"
              @update:model-value="updateCert(cert)"
            />
          </td>
          <td>
            <DateInput
              v-model="cert.IssueDate"
              class="cell-input"
              :disabled="!canWrite"
              @blur="updateCert(cert)"
            />
          </td>
          <td>{{ formatSize(cert.FileSizeBytes) }}</td>
          <td>{{ new Date(cert.UploadedDate).toLocaleString("ru-RU") }}</td>
          <td class="actions">
            <button v-if="canWrite" class="link-btn" @click="download(cert)">Скачать</button>
            <button v-if="canWrite" class="link-btn delete-btn" @click="remove(cert)">Удалить</button>
          </td>
        </tr>
        <tr v-if="certificates.length === 0">
          <td colspan="7" class="empty">Аттестатов пока нет</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.upload-form {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}
.file-btn {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
  white-space: nowrap;
}
.text-input,
.date-input {
  padding: 0.5rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.85rem;
}
.level-select {
  min-width: 260px;
}
.primary-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
  font-size: 0.85rem;
}
.primary-btn:disabled {
  opacity: 0.5;
  cursor: default;
}
.grid {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}
.grid th,
.grid td {
  text-align: left;
  padding: 0.5rem 0.7rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.85rem;
}
.level-cell {
  min-width: 220px;
}
.cell-input {
  padding: 0.35rem 0.5rem;
  border: 1px solid transparent;
  border-radius: 4px;
  font-size: 0.85rem;
  width: 100%;
  box-sizing: border-box;
}
.cell-input:hover,
.cell-input:focus {
  border-color: #cbd5e1;
}
.link-btn {
  border: none;
  background: none;
  color: #2563eb;
  cursor: pointer;
  padding: 0;
  margin-right: 0.75rem;
  font-size: 0.8rem;
}
.delete-btn {
  color: #dc2626;
}
.empty {
  text-align: center;
  color: #94a3b8;
  padding: 1.5rem;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}
</style>
