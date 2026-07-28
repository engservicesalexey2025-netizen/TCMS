<script setup>
import { onMounted, ref } from "vue";
import apiClient from "../api/client";

const requests = ref([]);
const roles = ref([]);
const lastDecision = ref(null);

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

async function decide(request, approve) {
  const { data } = await apiClient.post(`/access-requests/${request.Id}/decide`, {
    Approve: approve,
  });
  if (approve) {
    lastDecision.value = data.Comment;
  }
  await load();
}

onMounted(load);
</script>

<template>
  <div>
    <h2>Заявки на доступ</h2>
    <p v-if="lastDecision" class="notice">{{ lastDecision }}</p>
    <table class="grid">
      <thead>
        <tr>
          <th>ФИО</th>
          <th>Email</th>
          <th>Запрошенная роль</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in requests" :key="r.Id">
          <td>{{ r.FullName }}</td>
          <td>{{ r.Email }}</td>
          <td>{{ roleName(r.RequestedRoleId) }}</td>
          <td class="actions">
            <button class="link-btn approve" @click="decide(r, true)">Одобрить</button>
            <button class="link-btn reject" @click="decide(r, false)">Отклонить</button>
          </td>
        </tr>
        <tr v-if="requests.length === 0">
          <td colspan="4" class="empty">Нет заявок на рассмотрении</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.notice {
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  color: #065f46;
  padding: 0.75rem 1rem;
  border-radius: 8px;
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
.link-btn {
  border: none;
  background: none;
  cursor: pointer;
  padding: 0;
  margin-right: 0.75rem;
  font-size: 0.85rem;
}
.approve {
  color: #16a34a;
}
.reject {
  color: #dc2626;
}
.empty {
  text-align: center;
  color: #94a3b8;
  padding: 1.5rem;
}
</style>
