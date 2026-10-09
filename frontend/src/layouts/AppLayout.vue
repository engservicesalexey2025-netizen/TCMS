<script setup>
import { computed } from "vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();

const navItems = [
  { to: "/", label: "Главная", icon: "pi pi-home", permission: null },
  { to: "/employees", label: "Сотрудники", icon: "pi pi-users", permission: { module: "EMPLOYEES", action: "VIEW" } },
  { to: "/projects", label: "Проекты", icon: "pi pi-building", permission: { module: "PROJECTS", action: "VIEW" } },
  { to: "/contractors", label: "Подрядчики", icon: "pi pi-briefcase", permission: { module: "CONTRACTORS", action: "VIEW" } },
  { to: "/assignments", label: "Назначения", icon: "pi pi-id-card", permission: { module: "ASSIGNMENTS", action: "VIEW" } },
  { to: "/remarks", label: "Замечания", icon: "pi pi-exclamation-triangle", permission: { module: "REMARKS", action: "VIEW" } },
  { to: "/imports", label: "История импортов", icon: "pi pi-upload", permission: null },
];

// Технический отдел — отдельная группа с особыми условиями редактирования
// (права по KPI/WORKLOAD_NORMS назначает Администратор через Роли и права).
const technicalNavItems = [
  { to: "/kpi", label: "KPI", icon: "pi pi-chart-bar", permission: { module: "KPI", action: "VIEW" } },
  {
    to: "/kpi/departments",
    label: "KPI ТН Подразделения",
    icon: "pi pi-sitemap",
    permission: { module: "KPI", action: "VIEW" },
  },
  {
    to: "/workload-additional",
    label: "Дополнительные нагрузки ТН",
    icon: "pi pi-file-excel",
    permission: { module: "WORKLOAD_NORMS", action: "VIEW" },
  },
];

const adminNavItems = [
  { to: "/org-units", label: "Оргструктура", icon: "pi pi-sitemap", permission: { module: "ORG_UNITS", action: "VIEW" } },
  { to: "/admin/reference-data", label: "Справочники", icon: "pi pi-list", permission: { module: "POSITIONS", action: "VIEW" } },
  { to: "/access-requests", label: "Заявки на доступ", icon: "pi pi-user-plus", permission: { module: "ACCESS_REQUESTS", action: "VIEW" } },
  { to: "/admin/users", label: "Пользователи", icon: "pi pi-users", permission: { module: "USERS", action: "VIEW" } },
  { to: "/admin/roles", label: "Роли и права", icon: "pi pi-shield", permission: { module: "ROLES", action: "MANAGE" } },
  { to: "/admin/security-log", label: "Журнал безопасности", icon: "pi pi-history", permission: { module: "SECURITY_LOG", action: "VIEW" } },
];

const visibleNavItems = computed(() =>
  navItems.filter((item) => !item.permission || auth.can(item.permission.module, item.permission.action)),
);
const visibleTechnicalNavItems = computed(() =>
  technicalNavItems.filter((item) => !item.permission || auth.can(item.permission.module, item.permission.action)),
);
const showTechnicalSection = computed(() => visibleTechnicalNavItems.value.length > 0);
const visibleAdminNavItems = computed(() =>
  adminNavItems.filter((item) => !item.permission || auth.can(item.permission.module, item.permission.action)),
);
const showAdminSection = computed(() => visibleAdminNavItems.value.length > 0);

const roleNames = computed(() => auth.roles.map((r) => r.Name).join(", "));

async function logout() {
  await auth.logout();
}

async function exitViewAs() {
  const original = localStorage.getItem("tcms_token_original");
  if (!original) return;
  const { setToken } = await import("../services/tokenStorage");
  setToken(original, true);
  localStorage.removeItem("tcms_token_original");
  auth.token = original;
  await auth.fetchMe();
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">TSMS</div>
      <nav>
        <router-link v-for="item in visibleNavItems" :key="item.to" :to="item.to" class="nav-link">
          <i :class="item.icon"></i> {{ item.label }}
        </router-link>
        <template v-if="showTechnicalSection">
          <div class="nav-section-title">Технический отдел</div>
          <router-link v-for="item in visibleTechnicalNavItems" :key="item.to" :to="item.to" class="nav-link">
            <i :class="item.icon"></i> {{ item.label }}
          </router-link>
        </template>
        <template v-if="showAdminSection">
          <div class="nav-section-title">Администрирование</div>
          <router-link v-for="item in visibleAdminNavItems" :key="item.to" :to="item.to" class="nav-link">
            <i :class="item.icon"></i> {{ item.label }}
          </router-link>
        </template>
      </nav>
    </aside>
    <div class="main">
      <div v-if="auth.isViewingAs" class="view-as-banner">
        Вы просматриваете как: {{ auth.user?.Login }} ({{ roleNames }})
        <button type="button" @click="exitViewAs">Выйти из режима</button>
      </div>
      <header class="topbar">
        <router-link to="/profile" class="user-link">{{ auth.user?.Login }} · {{ roleNames }}</router-link>
        <button class="logout-btn" @click="logout">Выйти</button>
      </header>
      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: 240px;
  flex-shrink: 0;
  background: #1e2b3a;
  color: #fff;
  display: flex;
  flex-direction: column;
}
.brand {
  font-size: 1.25rem;
  font-weight: 700;
  padding: 1.25rem 1rem;
}
nav {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  padding: 0 0.5rem;
}
.nav-link {
  color: #cdd7e1;
  text-decoration: none;
  padding: 0.6rem 0.75rem;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.nav-link:hover,
.nav-link.router-link-exact-active {
  background: #2c4054;
  color: #fff;
}
.nav-section-title {
  margin-top: 0.75rem;
  padding: 0.4rem 0.75rem;
  font-size: 0.75rem;
  text-transform: uppercase;
  color: #7c8ea0;
}
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.view-as-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  background: #f59e0b;
  color: #1e293b;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.5rem 1rem;
}
.view-as-banner button {
  border: none;
  background: #1e293b;
  color: #fff;
  padding: 0.3rem 0.8rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}
.topbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
}
.user-link {
  color: #334155;
  text-decoration: none;
  font-size: 0.9rem;
}
.user-link:hover {
  text-decoration: underline;
}
.logout-btn {
  border: none;
  background: #ef4444;
  color: #fff;
  padding: 0.4rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
}
.content {
  padding: 1.5rem;
  overflow-x: auto;
}
</style>
