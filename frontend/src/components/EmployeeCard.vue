<script setup>
import { useRouter } from "vue-router";
import { EMPLOYEE_STATUS } from "../constants/employeeStatus";

const props = defineProps({
  employee: { type: Object, required: true },
  positionLabel: { type: String, default: "" },
  cityLabel: { type: String, default: "" },
  legalEntityLabel: { type: String, default: "" },
});

const router = useRouter();

function open() {
  router.push(`/employees/${props.employee.Id}`);
}
</script>

<template>
  <div class="employee-card" @click="open">
    <div class="card-header">
      <span class="full-name">{{ employee.FullName }}</span>
      <span
        class="status-badge"
        :style="{ background: EMPLOYEE_STATUS[employee.Status]?.color || '#94a3b8' }"
      >
        {{ EMPLOYEE_STATUS[employee.Status]?.label || employee.Status }}
      </span>
    </div>
    <div class="card-body">
      <div v-if="positionLabel" class="field">{{ positionLabel }}</div>
      <div v-if="cityLabel" class="field">{{ cityLabel }}</div>
      <div v-if="legalEntityLabel" class="field">{{ legalEntityLabel }}</div>
    </div>
  </div>
</template>

<style scoped>
.employee-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  cursor: pointer;
  transition: box-shadow 0.15s;
}
.employee-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.6rem;
}
.full-name {
  font-weight: 600;
  color: #1e2b3a;
}
.status-badge {
  flex-shrink: 0;
  padding: 0.15rem 0.6rem;
  border-radius: 999px;
  color: #fff;
  font-size: 0.75rem;
  white-space: nowrap;
}
.card-body {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.85rem;
  color: #64748b;
}
</style>
