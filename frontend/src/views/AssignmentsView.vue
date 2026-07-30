<script setup>
import { computed, onMounted, ref } from "vue";
import apiClient from "../api/client";
import EntityTable from "../components/EntityTable.vue";
import { useAuthStore } from "../stores/auth";
import { ASSIGNMENT_STATUS } from "../constants/assignmentStatus";

const auth = useAuthStore();
// Импорт/экспорт для назначений сегодня не подключены на бэкенде (нет
// профиля импорта и /assignments/export) — не выставляем эти права
// независимо от прав роли, чтобы кнопка не вела в никуда.
const tablePermissions = computed(() => ({
  create: auth.can("ASSIGNMENTS", "CREATE"),
  edit: auth.can("ASSIGNMENTS", "UPDATE"),
  delete: auth.can("ASSIGNMENTS", "DELETE"),
  import: false,
  export: false,
}));

const employees = ref([]);
const projects = ref([]);
const assignmentRoles = ref([]);

onMounted(async () => {
  const [employeesRes, projectsRes, rolesRes] = await Promise.all([
    apiClient.get("/employees", { params: { limit: 500 } }),
    apiClient.get("/projects", { params: { limit: 500 } }),
    apiClient.get("/assignment-roles", { params: { limit: 500 } }),
  ]);
  employees.value = employeesRes.data.items;
  projects.value = projectsRes.data.items;
  assignmentRoles.value = rolesRes.data.items;
});

const employeeOptions = computed(() =>
  employees.value.map((e) => ({ label: e.FullName, value: e.Id })),
);
const projectOptions = computed(() =>
  projects.value.map((p) => ({ label: p.Name, value: p.Id })),
);
const assignmentRoleOptions = computed(() =>
  assignmentRoles.value.map((r) => ({ label: r.Name, value: r.Id })),
);

const columns = computed(() => [
  { field: "EmployeeId", header: "Сотрудник", options: employeeOptions.value },
  { field: "ProjectId", header: "Проект", options: projectOptions.value },
  { field: "RoleOnProjectId", header: "Роль на проекте", options: assignmentRoleOptions.value },
  { field: "Workload", header: "Загрузка" },
  { field: "PeriodStart", header: "Начало на проекте" },
  { field: "PeriodEnd", header: "Окончание на проекте" },
  {
    field: "AssignmentStatus",
    header: "Статус на проекте",
    type: "badge",
    map: ASSIGNMENT_STATUS,
    badgeKey: (row) => (row.PeriodEnd ? "COMPLETED" : "ACTIVE"),
  },
]);

const formFields = computed(() => [
  { field: "EmployeeId", label: "Сотрудник", type: "select", options: employeeOptions.value },
  { field: "ProjectId", label: "Проект", type: "select", options: projectOptions.value },
  {
    field: "RoleOnProjectId",
    label: "Роль на проекте",
    type: "creatable-select",
    options: assignmentRoleOptions.value,
    createEndpoint: "/assignment-roles",
    onCreated: (opt) => assignmentRoles.value.push({ Id: opt.value, Name: opt.label }),
    onDeleted: (id) => (assignmentRoles.value = assignmentRoles.value.filter((r) => r.Id !== id)),
  },
  { field: "Workload", label: "Загрузка (0-1)", type: "number" },
  { field: "PeriodStart", label: "Начало на проекте", type: "date" },
  { field: "PeriodEnd", label: "Окончание на проекте", type: "date" },
]);
</script>

<template>
  <EntityTable
    resource="/assignments"
    title="Назначения"
    :columns="columns"
    :form-fields="formFields"
    :permissions="tablePermissions"
  />
</template>
