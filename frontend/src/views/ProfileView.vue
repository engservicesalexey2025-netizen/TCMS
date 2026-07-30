<script setup>
import { onMounted, ref } from "vue";
import apiClient from "../api/client";
import ActiveSessionsTab from "../components/ActiveSessionsTab.vue";
import ChangePasswordForm from "../components/ChangePasswordForm.vue";
import DelegationTab from "../components/DelegationTab.vue";
import TwoFactorSetup from "../components/TwoFactorSetup.vue";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();
const activeTab = ref("profile");
const profile = ref(null);

const historyItems = ref([]);
const historyTotal = ref(0);
const historySkip = ref(0);
const historyLimit = ref(20);

async function loadProfile() {
  const { data } = await apiClient.get("/profile/me");
  profile.value = data;
}

async function loadHistory() {
  const { data } = await apiClient.get("/auth/login-history", {
    params: { skip: historySkip.value, limit: historyLimit.value },
  });
  historyItems.value = data.items;
  historyTotal.value = data.total;
}

function selectTab(tab) {
  activeTab.value = tab;
  if (tab === "history" && historyItems.value.length === 0) loadHistory();
}

onMounted(loadProfile);
</script>

<template>
  <div class="profile-page">
    <h2>Личный кабинет</h2>

    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'profile' }]" @click="selectTab('profile')">Профиль</button>
      <button :class="['tab-btn', { active: activeTab === 'password' }]" @click="selectTab('password')">Изменить пароль</button>
      <button :class="['tab-btn', { active: activeTab === 'history' }]" @click="selectTab('history')">История входов</button>
      <button :class="['tab-btn', { active: activeTab === 'sessions' }]" @click="selectTab('sessions')">Активные устройства</button>
      <button :class="['tab-btn', { active: activeTab === 'mfa' }]" @click="selectTab('mfa')">Двухфакторная аутентификация</button>
      <button :class="['tab-btn', { active: activeTab === 'delegation' }]" @click="selectTab('delegation')">Делегирование</button>
      <button :class="['tab-btn', { active: activeTab === 'notifications' }]" @click="selectTab('notifications')">Уведомления</button>
    </div>

    <section v-if="activeTab === 'profile' && profile" class="card">
      <dl class="profile-grid">
        <dt>ФИО</dt>
        <dd>{{ profile.FullName || "—" }}</dd>
        <dt>Логин</dt>
        <dd>{{ profile.Login }}</dd>
        <dt>Email</dt>
        <dd>{{ profile.Email }}</dd>
        <dt>Должность</dt>
        <dd>{{ profile.Position || "—" }}</dd>
        <dt>Подразделение</dt>
        <dd>{{ profile.OrgUnit || "—" }}</dd>
        <dt>Роли</dt>
        <dd>{{ profile.Roles.join(", ") || "—" }}</dd>
        <dt>Последний вход</dt>
        <dd>{{ profile.LastLoginAt ? new Date(profile.LastLoginAt).toLocaleString("ru-RU") : "—" }}</dd>
        <dt>Активные проекты</dt>
        <dd>
          <span v-if="profile.ActiveProjects.length === 0">—</span>
          <span v-else>{{ profile.ActiveProjects.map((p) => p.Name).join(", ") }}</span>
        </dd>
      </dl>
    </section>

    <section v-else-if="activeTab === 'password'" class="card">
      <ChangePasswordForm />
    </section>

    <section v-else-if="activeTab === 'history'" class="card">
      <table class="grid">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Логин</th>
            <th>Результат</th>
            <th>IP</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="h in historyItems" :key="h.Id">
            <td>{{ new Date(h.CreatedDate).toLocaleString("ru-RU") }}</td>
            <td>{{ h.LoginAttempted }}</td>
            <td :class="h.Success ? 'success' : 'failure'">{{ h.Success ? "Успешно" : (h.Reason || "Ошибка") }}</td>
            <td>{{ h.IpAddress || "—" }}</td>
          </tr>
          <tr v-if="historyItems.length === 0">
            <td colspan="4" class="empty">История пуста</td>
          </tr>
        </tbody>
      </table>
      <div class="pager">
        <button :disabled="historySkip === 0" @click="historySkip = Math.max(0, historySkip - historyLimit); loadHistory()">← Назад</button>
        <span>{{ historySkip + 1 }}–{{ Math.min(historySkip + historyLimit, historyTotal) }} из {{ historyTotal }}</span>
        <button :disabled="historySkip + historyLimit >= historyTotal" @click="historySkip += historyLimit; loadHistory()">Вперёд →</button>
      </div>
    </section>

    <section v-else-if="activeTab === 'sessions'" class="card">
      <ActiveSessionsTab />
    </section>

    <section v-else-if="activeTab === 'mfa'" class="card">
      <TwoFactorSetup />
    </section>

    <section v-else-if="activeTab === 'delegation'" class="card">
      <DelegationTab />
    </section>

    <section v-else-if="activeTab === 'notifications'" class="card">
      <p class="stub">Раздел находится в разработке.</p>
    </section>
  </div>
</template>

<style scoped>
.profile-page h2 {
  margin: 0 0 1rem;
}
.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}
.tab-btn {
  border: 1px solid #cbd5e1;
  background: #fff;
  padding: 0.4rem 0.9rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  color: #334155;
}
.tab-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}
.card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.5rem;
}
.profile-grid {
  display: grid;
  grid-template-columns: 200px 1fr;
  row-gap: 0.75rem;
  margin: 0;
}
.profile-grid dt {
  color: #64748b;
  font-size: 0.85rem;
}
.profile-grid dd {
  margin: 0;
  font-size: 0.9rem;
  color: #1e293b;
}
.grid {
  width: 100%;
  border-collapse: collapse;
}
.grid th,
.grid td {
  text-align: left;
  padding: 0.5rem 0.7rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.85rem;
}
.success {
  color: #16a34a;
}
.failure {
  color: #dc2626;
}
.empty {
  text-align: center;
  color: #94a3b8;
  padding: 1.5rem;
}
.pager {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.75rem;
  font-size: 0.85rem;
  color: #475569;
}
.stub {
  color: #94a3b8;
}
</style>
