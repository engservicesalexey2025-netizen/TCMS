<script setup>
import { computed, ref } from "vue";
import EntityTable from "../../components/EntityTable.vue";
import { useAuthStore } from "../../stores/auth";

const auth = useAuthStore();

// Все справочники ниже уже имеют полноценный CRUD-роутер на бэкенде
// (build_crud_router) — здесь просто единая витрина для их редактирования
// администратором, вместо создания "на лету" через CreatableSelect внутри
// карточек Сотрудника/Проекта. Форма везде одинаковая (Название+Комментарий),
// т.к. таковы сегодняшние схемы этих таблиц.
const CATALOGS = [
  { key: "positions", title: "Должности", resource: "/positions", module: "POSITIONS", importResource: "positions" },
  { key: "cities", title: "Города", resource: "/cities", module: "CITIES" },
  { key: "legal-entities", title: "Юридические лица (ТОО)", resource: "/legal-entities", module: "LEGAL_ENTITIES" },
  { key: "certification-levels", title: "Уровни аттестации", resource: "/certification-levels", module: "CERTIFICATION_LEVELS" },
  { key: "project-types", title: "Типы проектов", resource: "/project-types", module: "PROJECT_TYPES" },
  { key: "project-stages", title: "Стадии проектов", resource: "/project-stages", module: "PROJECT_STAGES" },
  { key: "contours", title: "Контуры", resource: "/contours", module: "CONTOURS" },
  { key: "control-systems", title: "Системы контроля", resource: "/control-systems", module: "CONTROL_SYSTEMS" },
  { key: "assignment-roles", title: "Роли на проекте", resource: "/assignment-roles", module: "ASSIGNMENT_ROLES" },
];

const visibleCatalogs = computed(() =>
  CATALOGS.filter((c) => auth.can(c.module, "VIEW")),
);

const activeKey = ref(visibleCatalogs.value[0]?.key ?? null);
const activeCatalog = computed(() =>
  visibleCatalogs.value.find((c) => c.key === activeKey.value) ?? null,
);

const columns = [{ field: "Name", header: "Название" }];
const formFields = [
  { field: "Name", label: "Название", type: "text" },
  { field: "Comment", label: "Комментарий", type: "text" },
];

const tablePermissions = computed(() => {
  const module = activeCatalog.value?.module;
  if (!module) return { create: false, edit: false, delete: false, import: false, export: false };
  return {
    create: auth.can(module, "CREATE"),
    edit: auth.can(module, "UPDATE"),
    delete: auth.can(module, "DELETE"),
    import: auth.can(module, "IMPORT"),
    export: auth.can(module, "EXPORT"),
  };
});
</script>

<template>
  <div class="reference-data">
    <h2>Справочники</h2>
    <div class="layout">
      <aside class="catalog-list">
        <button
          v-for="c in visibleCatalogs"
          :key="c.key"
          :class="['catalog-btn', { active: c.key === activeKey }]"
          @click="activeKey = c.key"
        >
          {{ c.title }}
        </button>
        <p v-if="visibleCatalogs.length === 0" class="empty">Нет доступных справочников</p>
      </aside>
      <main class="catalog-panel">
        <EntityTable
          v-if="activeCatalog"
          :key="activeCatalog.key"
          :resource="activeCatalog.resource"
          :title="activeCatalog.title"
          :columns="columns"
          :form-fields="formFields"
          :permissions="tablePermissions"
          :import-resource="activeCatalog.importResource || null"
        />
        <p v-else class="empty">Выберите справочник слева</p>
      </main>
    </div>
  </div>
</template>

<style scoped>
.reference-data h2 {
  margin: 0 0 1rem;
}
.layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 1.25rem;
  align-items: start;
}
.catalog-list {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 0.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}
.catalog-btn {
  text-align: left;
  border: none;
  background: none;
  padding: 0.55rem 0.7rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.88rem;
  color: #334155;
}
.catalog-btn:hover {
  background: #f1f5f9;
}
.catalog-btn.active {
  background: #dbeafe;
  color: #1d4ed8;
  font-weight: 600;
}
.catalog-panel {
  min-width: 0;
}
.empty {
  color: #94a3b8;
  font-size: 0.85rem;
  text-align: center;
  padding: 1rem 0;
}
</style>
