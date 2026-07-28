<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const router = useRouter();

const isAdmin = computed(() => auth.roleCode === "ADMIN");

const navItems = [
  { to: "/", label: "Главная", icon: "pi pi-home" },
  { to: "/employees", label: "Сотрудники", icon: "pi pi-users" },
  { to: "/projects", label: "Проекты", icon: "pi pi-building" },
  { to: "/objects", label: "Объекты", icon: "pi pi-map-marker" },
  { to: "/contractors", label: "Подрядчики", icon: "pi pi-briefcase" },
  { to: "/assignments", label: "Назначения", icon: "pi pi-id-card" },
  { to: "/remarks", label: "Замечания", icon: "pi pi-exclamation-triangle" },
  { to: "/imports", label: "История импортов", icon: "pi pi-upload" },
];

const adminNavItems = [
  { to: "/org-units", label: "Оргструктура", icon: "pi pi-sitemap" },
  { to: "/access-requests", label: "Заявки на доступ", icon: "pi pi-user-plus" },
];

function logout() {
  auth.logout();
  router.push({ name: "login" });
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">TCMS</div>
      <nav>
        <router-link
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-link"
        >
          <i :class="item.icon"></i> {{ item.label }}
        </router-link>
        <template v-if="isAdmin">
          <div class="nav-section-title">Администрирование</div>
          <router-link
            v-for="item in adminNavItems"
            :key="item.to"
            :to="item.to"
            class="nav-link"
          >
            <i :class="item.icon"></i> {{ item.label }}
          </router-link>
        </template>
      </nav>
    </aside>
    <div class="main">
      <header class="topbar">
        <span>{{ auth.user?.Login }} · {{ auth.roleCode }}</span>
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
.topbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1.5rem;
  border-bottom: 1px solid #e2e8f0;
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
