<script setup>
import { computed, onMounted, ref } from "vue";
import apiClient from "../api/client";
import EntityTable from "../components/EntityTable.vue";

const employees = ref([]);
const projects = ref([]);

onMounted(async () => {
  const [employeesRes, projectsRes] = await Promise.all([
    apiClient.get("/employees", { params: { limit: 500 } }),
    apiClient.get("/projects", { params: { limit: 500 } }),
  ]);
  employees.value = employeesRes.data.items;
  projects.value = projectsRes.data.items;
});

const employeeOptions = computed(() =>
  employees.value.map((e) => ({ label: e.FullName, value: e.Id })),
);
const projectOptions = computed(() =>
  projects.value.map((p) => ({ label: p.Name, value: p.Id })),
);

const columns = computed(() => [
  { field: "EmployeeId", header: "Сотрудник", options: employeeOptions.value },
  { field: "ProjectId", header: "Проект", options: projectOptions.value },
  { field: "RoleOnProject", header: "Роль на проекте" },
  { field: "Workload", header: "Загрузка" },
]);

const formFields = computed(() => [
  { field: "EmployeeId", label: "Сотрудник", type: "select", options: employeeOptions.value },
  { field: "ProjectId", label: "Проект", type: "select", options: projectOptions.value },
  { field: "RoleOnProject", label: "Роль на проекте", type: "text" },
  { field: "Workload", label: "Загрузка (0-1)", type: "number" },
  { field: "PeriodStart", label: "Начало периода", type: "date" },
  { field: "PeriodEnd", label: "Конец периода", type: "date" },
]);
</script>

<template>
  <EntityTable
    resource="/assignments"
    title="Назначения"
    :columns="columns"
    :form-fields="formFields"
  />
</template>
