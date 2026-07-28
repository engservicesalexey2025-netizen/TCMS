<script setup>
import { computed, onMounted, ref } from "vue";
import apiClient from "../api/client";
import EntityTable from "../components/EntityTable.vue";

const orgUnits = ref([]);

onMounted(async () => {
  const { data } = await apiClient.get("/org-units", { params: { limit: 500 } });
  orgUnits.value = data.items;
});

const orgUnitOptions = computed(() =>
  orgUnits.value.map((u) => ({ label: u.Name, value: u.Id })),
);

const statusOptions = [
  { label: "Планируется", value: "PLANNED" },
  { label: "В работе", value: "IN_PROGRESS" },
  { label: "Завершён", value: "COMPLETED" },
  { label: "Приостановлен", value: "SUSPENDED" },
];

const columns = [
  { field: "Name", header: "Название" },
  { field: "Status", header: "Статус", options: statusOptions },
  { field: "StartDate", header: "Начало" },
];

const formFields = computed(() => [
  { field: "Name", label: "Название", type: "text" },
  { field: "OrgUnitId", label: "Оргединица", type: "select", options: orgUnitOptions.value },
  { field: "Area", label: "Площадь", type: "number" },
  { field: "Cost", label: "Стоимость", type: "number" },
  { field: "StartDate", label: "Дата начала", type: "date" },
  { field: "EndDate", label: "Дата окончания", type: "date" },
  { field: "Status", label: "Статус", type: "select", options: statusOptions, default: "PLANNED" },
]);
</script>

<template>
  <EntityTable
    resource="/projects"
    title="Проекты"
    :columns="columns"
    :form-fields="formFields"
  />
</template>
