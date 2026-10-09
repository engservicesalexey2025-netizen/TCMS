<script setup>
import { computed, ref } from "vue";
import apiClient from "../api/client";
import AdditionalWorkloadTab from "../components/AdditionalWorkloadTab.vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const canExport = computed(() => auth.can("WORKLOAD_NORMS", "EXPORT"));
const exporting = ref(false);

async function exportToExcel() {
  exporting.value = true;
  try {
    const response = await apiClient.get("/workload-norms/export", { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.download = "workload_norms_export.xlsx";
    link.click();
    window.URL.revokeObjectURL(url);
  } finally {
    exporting.value = false;
  }
}
</script>

<template>
  <div class="additional-workload-view">
    <div class="header">
      <h2>Дополнительные нагрузки ТН</h2>
      <button v-if="canExport" class="secondary-btn" :disabled="exporting" @click="exportToExcel">
        {{ exporting ? "Экспорт..." : "Экспорт в Excel" }}
      </button>
    </div>
    <AdditionalWorkloadTab />
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
.secondary-btn {
  padding: 0.5rem 1.1rem;
  border: 1px solid #2563eb;
  border-radius: 6px;
  background: #fff;
  color: #2563eb;
  cursor: pointer;
  font-size: 0.85rem;
}
.secondary-btn:disabled {
  opacity: 0.5;
  cursor: default;
}
</style>
