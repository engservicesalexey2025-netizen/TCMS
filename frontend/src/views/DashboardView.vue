<script setup>
import { onMounted, ref } from "vue";
import apiClient from "../api/client";

const counts = ref({ Employees: 0, Projects: 0, Remarks: 0 });

async function loadCount(resource) {
  const { data } = await apiClient.get(resource, { params: { limit: 1 } });
  return data.total;
}

onMounted(async () => {
  const [employees, projects, remarks] = await Promise.all([
    loadCount("/employees"),
    loadCount("/projects"),
    loadCount("/remarks"),
  ]);
  counts.value = { Employees: employees, Projects: projects, Remarks: remarks };
});
</script>

<template>
  <div>
    <h2>Главная</h2>
    <div class="cards">
      <div class="stat-card">
        <div class="stat-value">{{ counts.Employees }}</div>
        <div class="stat-label">Сотрудники</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ counts.Projects }}</div>
        <div class="stat-label">Проекты</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ counts.Remarks }}</div>
        <div class="stat-label">Замечания</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.cards {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}
.stat-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.25rem 1.75rem;
  min-width: 140px;
}
.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #1e2b3a;
}
.stat-label {
  color: #64748b;
  font-size: 0.9rem;
}
</style>
