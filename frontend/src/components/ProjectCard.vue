<script setup>
import { useRouter } from "vue-router";
import { PROJECT_STATUS } from "../constants/projectStatus";

const props = defineProps({
  project: { type: Object, required: true },
  cityLabel: { type: String, default: "" },
  orgUnitLabel: { type: String, default: "" },
  projectTypeLabel: { type: String, default: "" },
});

const router = useRouter();

function open() {
  router.push(`/projects/${props.project.Id}`);
}
</script>

<template>
  <div class="project-card" @click="open">
    <div class="card-header">
      <span class="name">{{ project.Name }}</span>
      <span
        class="status-badge"
        :style="{ background: PROJECT_STATUS[project.Status]?.color || '#94a3b8' }"
      >
        {{ PROJECT_STATUS[project.Status]?.label || project.Status }}
      </span>
    </div>
    <div class="card-body">
      <div v-if="cityLabel" class="field">{{ cityLabel }}</div>
      <div v-if="project.Address" class="field">{{ project.Address }}</div>
      <div v-if="orgUnitLabel" class="field">{{ orgUnitLabel }}</div>
      <div v-if="projectTypeLabel" class="field">{{ projectTypeLabel }}</div>
    </div>
  </div>
</template>

<style scoped>
.project-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1rem 1.25rem;
  cursor: pointer;
  transition: box-shadow 0.15s;
}
.project-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.6rem;
}
.name {
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
