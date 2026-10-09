<script setup>
// Реестр «кто за кем идёт»: та же иерархия, что и дерево подразделений,
// но развёрнута построчно с должностью и ФИО на каждом уровне — по
// референсу клиента (оргчарт с фото/подписями), без самого дерева карточек.
defineOptions({ name: "OrgUnitFullList" });

defineProps({
  nodes: { type: Array, required: true },
});
const emit = defineEmits(["select"]);

const TYPE_LABELS = {
  DIVISION: "Дивизион",
  CITY: "Город",
  DEPARTMENT: "Управление",
  GROUP: "Группа",
};
const MANAGER_LABELS = {
  DIVISION: "Руководитель дивизиона",
  CITY: "Директор филиала",
  DEPARTMENT: "Руководитель управления",
  GROUP: "Руководитель группы",
};
const TYPE_ICON = {
  DIVISION: "🏬",
  CITY: "🏙️",
  DEPARTMENT: "🏛️",
  GROUP: "👥",
};
</script>

<template>
  <ul class="roster">
    <li v-for="node in nodes" :key="node.Id" class="node">
      <div class="node-card" @click="emit('select', node.Id)">
        <div class="node-header">
          <span class="icon">{{ TYPE_ICON[node.UnitType] || "📁" }}</span>
          <span class="name">{{ node.Name }}</span>
          <span class="type-badge">{{ TYPE_LABELS[node.UnitType] || node.UnitType }}</span>
        </div>
        <div class="manager-line">
          {{ MANAGER_LABELS[node.UnitType] || "Руководитель" }}:
          <strong>{{ node.ManagerName || "не назначен" }}</strong>
        </div>
        <ul v-if="node.Employees.length" class="employees">
          <li v-for="e in node.Employees" :key="e.Id">
            {{ e.PositionName || "Должность не указана" }} — {{ e.FullName }}
          </li>
        </ul>
      </div>
      <OrgUnitFullList
        v-if="node.Children.length"
        :nodes="node.Children"
        @select="(id) => emit('select', id)"
      />
    </li>
  </ul>
</template>

<style scoped>
.roster {
  list-style: none;
  margin: 0;
  padding-left: 1.5rem;
}
.roster > .node {
  border-left: 2.5px solid #94a3b8;
}
.node {
  position: relative;
  padding: 0.5rem 0 0.5rem 1rem;
}
.node::before {
  content: "";
  position: absolute;
  left: -2.5px;
  top: 1.3rem;
  width: 1rem;
  height: 2.5px;
  background: #94a3b8;
}
.node-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.6rem 0.9rem;
  cursor: pointer;
  transition: border-color 0.15s, box-shadow 0.15s;
  display: inline-block;
  min-width: 260px;
}
.node-card:hover {
  border-color: #2563eb;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
}
.node-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.3rem;
}
.icon {
  font-size: 1rem;
}
.name {
  font-weight: 600;
  color: #1e2b3a;
  font-size: 0.9rem;
}
.type-badge {
  background: #eff6ff;
  color: #2563eb;
  border-radius: 999px;
  padding: 0.05rem 0.55rem;
  font-size: 0.7rem;
}
.manager-line {
  font-size: 0.8rem;
  color: #475569;
}
.employees {
  list-style: none;
  margin: 0.4rem 0 0;
  padding: 0.4rem 0 0 0.75rem;
  border-top: 1px dashed #e2e8f0;
  font-size: 0.8rem;
  color: #334155;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}
</style>
