<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import apiClient from "../api/client";

const router = useRouter();
const requests = ref([]);
const roles = ref([]);

function roleName(id) {
  return roles.value.find((r) => r.Id === id)?.Name ?? id;
}

async function load() {
  const [reqRes, rolesRes] = await Promise.all([
    apiClient.get("/access-requests", { params: { status_filter: "PENDING", limit: 100 } }),
    apiClient.get("/public/roles"),
  ]);
  requests.value = reqRes.data.items;
  roles.value = rolesRes.data;
}

function openReview(request) {
  router.push({ name: "access-request-review", params: { id: request.Id } });
}

onMounted(load);
</script>

<template>
  <div>
    <h2>Заявки на доступ</h2>
    <table class="grid">
      <thead>
        <tr>
          <th>ФИО</th>
          <th>Email</th>
          <th>Организация</th>
          <th>Запрошенная роль</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in requests" :key="r.Id" class="clickable" @click="openReview(r)">
          <td>{{ r.FullName }}</td>
          <td>{{ r.Email }}</td>
          <td>{{ r.Organization || "—" }}</td>
          <td>{{ roleName(r.RequestedRoleId) }}</td>
          <td class="actions">
            <button class="link-btn" @click.stop="openReview(r)">Рассмотреть</button>
          </td>
        </tr>
        <tr v-if="requests.length === 0">
          <td colspan="5" class="empty">Нет заявок на рассмотрении</td>
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
.grid tr.clickable {
  cursor: pointer;
}
.grid tr.clickable:hover {
  background: #f8fafc;
}
.link-btn {
  border: none;
  background: none;
  color: #2563eb;
  cursor: pointer;
  padding: 0;
  font-size: 0.85rem;
}
.empty {
  text-align: center;
  color: #94a3b8;
  padding: 1.5rem;
}
</style>
