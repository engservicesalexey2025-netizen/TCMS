<script setup>
import { onMounted, ref } from "vue";
import apiClient from "../api/client";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();

const cards = [
  { key: "Employees", label: "Сотрудники", resource: "/employees", module: "EMPLOYEES" },
  { key: "Projects", label: "Проекты", resource: "/projects", module: "PROJECTS" },
  { key: "Remarks", label: "Замечания", resource: "/remarks", module: "REMARKS" },
];

const counts = ref({ Employees: null, Projects: null, Remarks: null });

async function loadCount(resource) {
  const { data } = await apiClient.get(resource, { params: { limit: 1 } });
  return data.total;
}

onMounted(() => {
  // На доступ к самому Дашборду прав не требуется, но у роли могут не быть
  // прав на часть карточек (например, у Наблюдателя нет PROJECTS/REMARKS) —
  // такие карточки просто пропускаем, а не валим всю страницу одним 403.
  cards
    .filter((card) => auth.can(card.module, "VIEW"))
    .forEach((card) => {
      loadCount(card.resource)
        .then((total) => {
          counts.value[card.key] = total;
        })
        .catch(() => {
          counts.value[card.key] = null;
        });
    });
});
</script>

<template>
  <div>
    <h2>Главная</h2>
    <div class="cards">
      <div v-for="card in cards.filter((c) => auth.can(c.module, 'VIEW'))" :key="card.key" class="stat-card">
        <div class="stat-value">{{ counts[card.key] ?? "—" }}</div>
        <div class="stat-label">{{ card.label }}</div>
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
