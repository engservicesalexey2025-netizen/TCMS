<script setup>
import { ref } from "vue";

// Явное имя нужно для рекурсивной самоссылки <OrgUnitTree> в шаблоне ниже —
// Vue SFC выводит имя из имени файла, но полагаться на это неявно рискованно.
defineOptions({ name: "OrgUnitTree" });

const props = defineProps({
  nodes: { type: Array, required: true },
  selectedId: { type: String, default: null },
});
const emit = defineEmits(["select"]);

const TYPE_ICON = {
  DIVISION: "🏬",
  CITY: "🏙️",
  DEPARTMENT: "🏛️",
  GROUP: "👥",
};

const collapsed = ref(new Set());

function toggle(id) {
  const next = new Set(collapsed.value);
  if (next.has(id)) next.delete(id);
  else next.add(id);
  collapsed.value = next;
}
</script>

<template>
  <ul class="tree">
    <li v-for="node in nodes" :key="node.Id">
      <div :class="['node', { active: node.Id === selectedId }]" @click="emit('select', node.Id)">
        <button
          v-if="node.Children?.length"
          class="toggle"
          @click.stop="toggle(node.Id)"
        >
          {{ collapsed.has(node.Id) ? "▶" : "▼" }}
        </button>
        <span v-else class="toggle-spacer"></span>
        <span class="icon">{{ TYPE_ICON[node.UnitType] || "📁" }}</span>
        <span class="name">{{ node.Name }}</span>
        <span v-if="node.EmployeeCount" class="count">{{ node.EmployeeCount }}</span>
        <span v-if="!node.IsActive" class="archived-badge">архив</span>
      </div>
      <OrgUnitTree
        v-if="node.Children?.length && !collapsed.has(node.Id)"
        :nodes="node.Children"
        :selected-id="selectedId"
        @select="(id) => emit('select', id)"
      />
    </li>
  </ul>
</template>

<style scoped>
.tree {
  list-style: none;
  margin: 0;
  padding-left: 1.1rem;
}
.tree:first-child {
  padding-left: 0;
}
.node {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.3rem 0.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.88rem;
  color: #334155;
}
.node:hover {
  background: #f1f5f9;
}
.node.active {
  background: #dbeafe;
  color: #1d4ed8;
  font-weight: 600;
}
.toggle {
  border: none;
  background: none;
  cursor: pointer;
  font-size: 0.65rem;
  color: #94a3b8;
  width: 1rem;
  padding: 0;
}
.toggle-spacer {
  width: 1rem;
  display: inline-block;
}
.icon {
  font-size: 0.9rem;
}
.name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.count {
  background: #e2e8f0;
  color: #475569;
  border-radius: 999px;
  padding: 0.05rem 0.5rem;
  font-size: 0.75rem;
}
.archived-badge {
  background: #fee2e2;
  color: #b91c1c;
  border-radius: 999px;
  padding: 0.05rem 0.5rem;
  font-size: 0.7rem;
}
</style>
