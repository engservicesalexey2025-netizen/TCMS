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
    path: "/forbidden",
    name: "forbidden",
    component: () => import("../views/ForbiddenView.vue"),
    meta: { public: true },
  },
  {
    path: "/",
    component: () => import("../layouts/AppLayout.vue"),
    children: [
      { path: "", name: "dashboard", component: () => import("../views/DashboardView.vue"), meta: { permission: null } },
      {
        path: "employees",
        name: "employees",
        component: () => import("../views/EmployeesView.vue"),
        meta: { permission: { module: "EMPLOYEES", action: "VIEW" } },
      },
      {
        path: "employees/:id",
        name: "employee-profile",
        component: () => import("../views/EmployeeProfileView.vue"),
        meta: { permission: { module: "EMPLOYEES", action: "VIEW" } },
      },
      {
        path: "projects",
        name: "projects",
        component: () => import("../views/ProjectsView.vue"),
        meta: { permission: { module: "PROJECTS", action: "VIEW" } },
      },
      {
        path: "projects/:id",
        name: "project-profile",
        component: () => import("../views/ProjectProfileView.vue"),
        meta: { permission: { module: "PROJECTS", action: "VIEW" } },
      },
      { path: "kpi", name: "kpi", component: () => import("../views/KpiView.vue"), meta: { permission: { module: "KPI", action: "VIEW" } } },
      {
        path: "kpi/departments",
        name: "kpi-departments",
        component: () => import("../views/KpiDepartmentsView.vue"),
        meta: { permission: { module: "KPI", action: "VIEW" } },
      },
      {
        path: "workload-additional",
        name: "workload-additional",
        component: () => import("../views/AdditionalWorkloadView.vue"),
        meta: { permission: { module: "WORKLOAD_NORMS", action: "VIEW" } },
      },
      {
        path: "contractors",
        name: "contractors",
        component: () => import("../views/ContractorsView.vue"),
        meta: { permission: { module: "CONTRACTORS", action: "VIEW" } },
      },
      {
        path: "assignments",
        name: "assignments",
        component: () => import("../views/AssignmentsView.vue"),
        meta: { permission: { module: "ASSIGNMENTS", action: "VIEW" } },
      },
      {
        path: "remarks",
        name: "remarks",
        component: () => import("../views/RemarksView.vue"),
        meta: { permission: { module: "REMARKS", action: "VIEW" } },
      },
      {
        path: "org-units",
        name: "org-units",
        component: () => import("../views/OrgUnitsView.vue"),
        meta: { permission: { module: "ORG_UNITS", action: "VIEW" } },
      },
      {
        path: "access-requests",
        name: "access-requests-admin",
        component: () => import("../views/AccessRequestsAdminView.vue"),
        meta: { permission: { module: "ACCESS_REQUESTS", action: "VIEW" } },
      },
      {
        path: "access-requests/:id",
        name: "access-request-review",
        component: () => import("../views/admin/AccessRequestReviewView.vue"),
        meta: { permission: { module: "ACCESS_REQUESTS", action: "UPDATE" } },
      },
      { path: "imports", name: "imports-history", component: () => import("../views/ImportHistoryView.vue"), meta: { permission: null } },
      { path: "imports/:entityType", name: "imports", component: () => import("../views/ImportView.vue"), meta: { permission: null } },
      { path: "profile", name: "profile", component: () => import("../views/ProfileView.vue"), meta: { permission: null } },
      {
        path: "admin/roles",
        name: "admin-roles",
        component: () => import("../views/admin/RolesView.vue"),
        meta: { permission: { module: "ROLES", action: "MANAGE" } },
      },
      {
        path: "admin/roles/:id",
        name: "admin-role-editor",
        component: () => import("../views/admin/RoleEditorView.vue"),
        meta: { permission: { module: "ROLES", action: "MANAGE" } },
      },
      {
        path: "admin/users",
        name: "admin-users",
        component: () => import("../views/admin/UsersView.vue"),
        meta: { permission: { module: "USERS", action: "VIEW" } },
      },
      {
        path: "admin/users/:id/permissions",
        name: "admin-user-permissions",
        component: () => import("../views/admin/UserPermissionsView.vue"),
        meta: { permission: { module: "USERS", action: "UPDATE" } },
      },
      {
        path: "admin/security-log",
        name: "admin-security-log",
        component: () => import("../views/admin/SecurityLogView.vue"),
        meta: { permission: { module: "SECURITY_LOG", action: "VIEW" } },
      },
      {
        path: "admin/reference-data",
        name: "admin-reference-data",
        component: () => import("../views/admin/ReferenceDataView.vue"),
        meta: { permission: { module: "POSITIONS", action: "VIEW" } },
      },
    ],
  },
  {
    path: "/change-password",
    name: "change-password",
    component: () => import("../views/ChangePasswordView.vue"),
    meta: { requiresAuthOnly: true },
  },
  {
    path: "/forgot-password",
    name: "forgot-password",
    component: () => import("../views/ForgotPasswordView.vue"),
    meta: { public: true },
  },
  {
    path: "/reset-password/:token",
    name: "reset-password",
    component: () => import("../views/ResetPasswordView.vue"),
    meta: { public: true },
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
      await auth.logout({ redirect: false });
      if (!to.meta.public) return { name: "login" };
    }
  }

  // Принудительная смена пароля (§6 ТЗ) блокирует всё, кроме самой этой
  // страницы и выхода, пока временный пароль не заменён.
  if (auth.mustChangePassword && to.name !== "change-password" && to.name !== "login") {
    return { name: "change-password" };
  }

  const perm = to.meta.permission;
  if (perm && !auth.can(perm.module, perm.action)) {
    return { name: "forbidden" };
  }

  return true;
});

export default router;
