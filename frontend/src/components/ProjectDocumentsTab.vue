<script setup>
import { onMounted, ref } from "vue";
import apiClient from "../api/client";

const props = defineProps({
  projectId: { type: String, required: true },
});

const MAX_DOCUMENTS = 5;

const documents = ref([]);
const uploading = ref(false);
const uploadError = ref("");
const fileInput = ref(null);

async function load() {
  const { data } = await apiClient.get(`/projects/${props.projectId}/documents`, {
    params: { limit: 100 },
  });
  documents.value = data.items;
}

function openFilePicker() {
  if (documents.value.length >= MAX_DOCUMENTS) return;
  fileInput.value?.click();
}

async function handleFileChange(event) {
  const file = event.target.files[0];
  event.target.value = "";
  if (!file) return;
  uploading.value = true;
  uploadError.value = "";
  try {
    const formData = new FormData();
    formData.append("file", file);
    await apiClient.post(`/projects/${props.projectId}/documents`, formData);
    await load();
  } catch (e) {
    uploadError.value = e.response?.data?.detail || "Ошибка загрузки файла";
  } finally {
    uploading.value = false;
  }
}

async function download(doc) {
  const response = await apiClient.get(
    `/projects/${props.projectId}/documents/${doc.Id}/download`,
    { responseType: "blob" },
  );
  const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
  window.open(url, "_blank");
}

async function remove(doc) {
  if (!window.confirm(`Удалить файл «${doc.FileName}»? Это действие необратимо.`)) {
    return;
  }
  await apiClient.delete(`/projects/${props.projectId}/documents/${doc.Id}`);
  await load();
}

onMounted(load);
</script>

<template>
  <div class="documents">
    <div v-for="doc in documents" :key="doc.Id" class="doc-row">
      <a class="doc-link" @click.prevent="download(doc)">{{ doc.FileName }}</a>
      <button class="remove-btn" title="Удалить" @click="remove(doc)">✗</button>
    </div>
    <p v-if="documents.length === 0" class="empty">Файлов пока нет</p>

    <button
      class="attach-btn"
      :disabled="uploading || documents.length >= MAX_DOCUMENTS"
      @click="openFilePicker"
    >
      {{ uploading ? "Загрузка..." : `Прикрепить PDF (макс. ${MAX_DOCUMENTS})` }}
    </button>
    <input
      ref="fileInput"
      type="file"
      accept="application/pdf"
      hidden
      @change="handleFileChange"
    />
    <p v-if="documents.length >= MAX_DOCUMENTS" class="hint">
      Достигнут лимит файлов на проект ({{ MAX_DOCUMENTS }}). Удалите файл, чтобы загрузить новый.
    </p>
    <p v-if="uploadError" class="error">{{ uploadError }}</p>
  </div>
</template>

<style scoped>
.documents {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.doc-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}
.doc-link {
  color: #2563eb;
  text-decoration: underline;
  cursor: pointer;
  font-size: 0.9rem;
  word-break: break-all;
}
.remove-btn {
  border: none;
  background: none;
  color: #f87171;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  padding: 0.2rem;
  flex-shrink: 0;
}
.remove-btn:hover {
  color: #dc2626;
}
.attach-btn {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: #fff;
  color: #334155;
  cursor: pointer;
  font-size: 0.9rem;
  margin-top: 0.5rem;
}
.attach-btn:disabled {
  opacity: 0.5;
  cursor: default;
}
.empty {
  color: #94a3b8;
  font-size: 0.85rem;
  margin: 0;
}
.hint {
  color: #ca8a04;
  font-size: 0.85rem;
  margin: 0.25rem 0 0;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
  margin: 0.25rem 0 0;
}
</style>
