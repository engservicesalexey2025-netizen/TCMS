<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import apiClient from "../../api/client";
import { useAuthStore } from "../../stores/auth";

const router = useRouter();
const auth = useAuthStore();
const users = ref([]);
const loading = ref(false);

async function load() {
  loading.value = true;
  try {
    const { data } = await apiClient.get("/users", { params: { limit: 200 } });
    users.value = data.items;
  } finally {
    loading.value = false;
  }
}

function openPermissions(user) {
  router.push({ name: "admin-user-permissions", params: { id: user.Id } });
}

async function viewAs(user) {
  if (!window.confirm(`Просмотреть систему от имени ${user.Login}? Режим строго для чтения.`)) return;
  const original = auth.token;
  const { data } = await apiClient.post(`/auth/view-as/${user.Id}`, { Reason: "Просмотр администратором" });
  localStorage.setItem("tcms_token_original", original);
  const { setToken } = await import("../../services/tokenStorage");
  setToken(data.access_token, true);
  auth.token = data.access_token;
  await auth.fetchMe();
  router.push({ name: "dashboard" });
}

onMounted(load);
</script>

<template>
  <div>
    <h2>Пользователи</h2>
    <table class="grid">
      <thead>
        <tr>
          <th>Логин</th>
          <th>Email</th>
          <th>Роли</th>
          <th>Активен</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.Id">
          <td>{{ u.Login }}</td>
          <td>{{ u.Email }}</td>
          <td>{{ u.Roles.join(", ") }}</td>
          <td>{{ u.IsActive ? "Да" : "Нет" }}</td>
          <td class="actions">
            <button class="link-btn" @click="openPermissions(u)">Права</button>
            <button v-if="auth.can('USERS', 'VIEW_AS')" class="link-btn" @click="viewAs(u)">Просмотреть как</button>
          </td>
        </tr>
        <tr v-if="!loading && users.length === 0">
          <td colspan="5" class="empty">Пользователей нет</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
h2 {
  margin: 0 0 1rem;
}
.grid {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}
.grid th,
.grid td {
  text-align: left;
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.9rem;
}
.actions {
  white-space: nowrap;
}
.link-btn {
  border: none;
  background: none;
  color: #2563eb;
  cursor: pointer;
  padding: 0;
  margin-right: 0.75rem;
  font-size: 0.85rem;
}
.empty {
  text-align: center;
  color: #94a3b8;
  padding: 1.5rem;
}
</style>
