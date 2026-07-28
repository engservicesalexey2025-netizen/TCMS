import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/auth";

const routes = [
  {
    path: "/login",
    name: "login",
    component: () => import("../views/LoginView.vue"),
    meta: { public: true },
  },
  {
    path: "/request-access",
    name: "request-access",
    component: () => import("../views/AccessRequestView.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    component: () => import("../layouts/AppLayout.vue"),
    children: [
      { path: "", name: "dashboard", component: () => import("../views/DashboardView.vue") },
      { path: "employees", name: "employees", component: () => import("../views/EmployeesView.vue") },
      { path: "employees/:id", name: "employee-profile", component: () => import("../views/EmployeeProfileView.vue") },
      { path: "projects", name: "projects", component: () => import("../views/ProjectsView.vue") },
      { path: "objects", name: "objects", component: () => import("../views/ObjectsView.vue") },
      { path: "contractors", name: "contractors", component: () => import("../views/ContractorsView.vue") },
      { path: "assignments", name: "assignments", component: () => import("../views/AssignmentsView.vue") },
      { path: "remarks", name: "remarks", component: () => import("../views/RemarksView.vue") },
      { path: "org-units", name: "org-units", component: () => import("../views/OrgUnitsView.vue") },
      { path: "access-requests", name: "access-requests-admin", component: () => import("../views/AccessRequestsAdminView.vue") },
      { path: "imports", name: "imports-history", component: () => import("../views/ImportHistoryView.vue") },
      { path: "imports/:entityType", name: "imports", component: () => import("../views/ImportView.vue") },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (!to.meta.public && !auth.isAuthenticated) {
    return { name: "login" };
  }
  if (auth.isAuthenticated && !auth.user) {
    try {
      await auth.fetchMe();
    } catch {
      auth.logout();
      if (!to.meta.public) return { name: "login" };
    }
  }
  return true;
});

export default router;
