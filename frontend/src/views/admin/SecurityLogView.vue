<script setup>
import EntityTable from "../../components/EntityTable.vue";

const READ_ONLY = { create: false, edit: false, delete: false, import: false, export: false };

const columns = [
  { field: "OccurredAt", header: "Дата/время", format: (v) => new Date(v).toLocaleString("ru-RU") },
  { field: "UserLogin", header: "Пользователь" },
  { field: "Action", header: "Действие" },
  { field: "Result", header: "Результат" },
  { field: "IpAddress", header: "IP" },
  { field: "Detail", header: "Детали" },
];
</script>

<template>
  <EntityTable
    resource="/security-log"
    title="Журнал безопасности"
    :columns="columns"
    :form-fields="[]"
    :permissions="READ_ONLY"
  />
</template>
