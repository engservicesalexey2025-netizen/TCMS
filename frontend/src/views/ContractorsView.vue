<script setup>
import { computed } from "vue";
import EntityTable from "../components/EntityTable.vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
// Импорт/экспорт для подрядчиков сегодня не подключены на бэкенде — не
// выставляем эти права независимо от прав роли.
const tablePermissions = computed(() => ({
  create: auth.can("CONTRACTORS", "CREATE"),
  edit: auth.can("CONTRACTORS", "UPDATE"),
  delete: auth.can("CONTRACTORS", "DELETE"),
  import: false,
  export: false,
}));

const columns = [
  { field: "Name", header: "Название" },
  { field: "BinIin", header: "БИН/ИИН" },
];

const formFields = [
  { field: "Name", label: "Название", type: "text" },
  { field: "BinIin", label: "БИН/ИИН", type: "text" },
  { field: "ContactInfo", label: "Контакты", type: "text" },
];
</script>

<template>
  <EntityTable
    resource="/contractors"
    title="Подрядчики"
    :columns="columns"
    :form-fields="formFields"
    :permissions="tablePermissions"
  />
</template>
