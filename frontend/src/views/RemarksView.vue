<script setup>
import { computed, onMounted, ref } from "vue";
import apiClient from "../api/client";
import EntityTable from "../components/EntityTable.vue";

const objects = ref([]);
const contractors = ref([]);
const employees = ref([]);

onMounted(async () => {
  const [objectsRes, contractorsRes, employeesRes] = await Promise.all([
    apiClient.get("/objects", { params: { limit: 500 } }),
    apiClient.get("/contractors", { params: { limit: 500 } }),
    apiClient.get("/employees", { params: { limit: 500 } }),
  ]);
  objects.value = objectsRes.data.items;
  contractors.value = contractorsRes.data.items;
  employees.value = employeesRes.data.items;
});

const objectOptions = computed(() => objects.value.map((o) => ({ label: o.Name, value: o.Id })));
const contractorOptions = computed(() => contractors.value.map((c) => ({ label: c.Name, value: c.Id })));
const employeeOptions = computed(() => employees.value.map((e) => ({ label: e.FullName, value: e.Id })));

const statusOptions = [
  { label: "Новое", value: "NEW" },
  { label: "В работе", value: "IN_PROGRESS" },
  { label: "Устранено", value: "RESOLVED" },
  { label: "Отклонено", value: "REJECTED" },
];

const columns = computed(() => [
  { field: "Title", header: "Замечание" },
  { field: "ObjectId", header: "Объект", options: objectOptions.value },
  { field: "Status", header: "Статус", options: statusOptions },
  { field: "DueDate", header: "Срок устранения" },
]);

const formFields = computed(() => [
  { field: "ObjectId", label: "Объект", type: "select", options: objectOptions.value },
  { field: "ContractorId", label: "Подрядчик", type: "select", options: contractorOptions.value },
  { field: "ResponsibleEmployeeId", label: "Ответственный", type: "select", options: employeeOptions.value },
  { field: "Title", label: "Заголовок", type: "text" },
  { field: "Description", label: "Описание", type: "text" },
  { field: "Status", label: "Статус", type: "select", options: statusOptions, default: "NEW" },
  { field: "DueDate", label: "Срок устранения", type: "date" },
]);
</script>

<template>
  <EntityTable
    resource="/remarks"
    title="Замечания"
    :columns="columns"
    :form-fields="formFields"
  />
</template>
