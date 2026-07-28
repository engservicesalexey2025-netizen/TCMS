<script setup>
import EntityTable from "../components/EntityTable.vue";

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
  />
</template>
