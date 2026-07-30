<script setup>
import { computed, onMounted, ref } from "vue";
import apiClient from "../api/client";
import EntityTable from "../components/EntityTable.vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
// Импорт/экспорт для оргструктуры сегодня не подключены на бэкенде — не
// выставляем эти права независимо от прав роли.
const tablePermissions = computed(() => ({
  create: auth.can("ORG_UNITS", "CREATE"),
  edit: auth.can("ORG_UNITS", "UPDATE"),
  delete: auth.can("ORG_UNITS", "DELETE"),
  import: false,
  export: false,
}));

const orgUnits = ref([]);

onMounted(async () => {
  const { data } = await apiClient.get("/org-units", { params: { limit: 500 } });
  orgUnits.value = data.items;
});

const parentOptions = computed(() =>
  orgUnits.value.map((u) => ({ label: u.Name, value: u.Id })),
);

const typeOptions = [
  { label: "Дивизион", value: "DIVISION" },
  { label: "Управление", value: "DEPARTMENT" },
  { label: "Группа", value: "GROUP" },
];

const columns = computed(() => [
  { field: "Name", header: "Название" },
  { field: "UnitType", header: "Тип", options: typeOptions },
  { field: "ParentOrgUnitId", header: "Родительская единица", options: parentOptions.value },
]);

const formFields = computed(() => [
  { field: "Name", label: "Название", type: "text" },
  { field: "UnitType", label: "Тип", type: "select", options: typeOptions },
  { field: "ParentOrgUnitId", label: "Родительская единица", type: "select", options: parentOptions.value },
]);
</script>

<template>
  <EntityTable
    resource="/org-units"
    title="Организационная структура"
    :columns="columns"
    :form-fields="formFields"
    :permissions="tablePermissions"
  />
</template>
