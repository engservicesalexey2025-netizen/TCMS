<script setup>
import { computed, onMounted, ref } from "vue";
import apiClient from "../api/client";
import EntityTable from "../components/EntityTable.vue";

const projects = ref([]);

onMounted(async () => {
  const { data } = await apiClient.get("/projects", { params: { limit: 500 } });
  projects.value = data.items;
});

const projectOptions = computed(() =>
  projects.value.map((p) => ({ label: p.Name, value: p.Id })),
);

const columns = [
  { field: "Name", header: "Название объекта" },
  { field: "Address", header: "Адрес" },
];

const formFields = computed(() => [
  { field: "ProjectId", label: "Проект", type: "select", options: projectOptions.value },
  { field: "Name", label: "Название объекта", type: "text" },
  { field: "Address", label: "Адрес", type: "text" },
]);
</script>

<template>
  <EntityTable
    resource="/objects"
    title="Объекты"
    :columns="columns"
    :form-fields="formFields"
  />
</template>
