<script setup>
import { ref } from "vue";
import apiClient from "../api/client";
import { useAuthStore } from "../stores/auth";

const auth = useAuthStore();

const step = ref("idle"); // idle | enrolling | enabled-once
const secret = ref("");
const provisioningUri = ref("");
const code = ref("");
const recoveryCodes = ref([]);
const disableCode = ref("");
const error = ref("");

async function startEnroll() {
  error.value = "";
  const { data } = await apiClient.post("/auth/mfa/setup");
  secret.value = data.Secret;
  provisioningUri.value = data.ProvisioningUri;
  step.value = "enrolling";
}

async function confirmEnable() {
  error.value = "";
  try {
    const { data } = await apiClient.post("/auth/mfa/enable", { Code: code.value });
    recoveryCodes.value = data.RecoveryCodes;
    step.value = "enabled-once";
    await auth.fetchMe();
  } catch (e) {
    error.value = e.response?.data?.detail || "Неверный код";
  }
}

async function disable() {
  error.value = "";
  try {
    await apiClient.post("/auth/mfa/disable", { Code: disableCode.value });
    disableCode.value = "";
    step.value = "idle";
    await auth.fetchMe();
  } catch (e) {
    error.value = e.response?.data?.detail || "Неверный код";
  }
}
</script>

<template>
  <div class="mfa">
    <p v-if="auth.is2FAEnabled && step !== 'enabled-once'" class="status enabled">
      Двухфакторная аутентификация включена.
    </p>

    <div v-if="auth.is2FAEnabled && step !== 'enabled-once'" class="disable-block">
      <label>
        Код из приложения (для отключения)
        <input v-model="disableCode" type="text" inputmode="numeric" maxlength="6" />
      </label>
      <button class="danger-btn" @click="disable">Отключить 2FA</button>
    </div>

    <template v-else-if="!auth.is2FAEnabled">
      <p v-if="step === 'idle'" class="status">Двухфакторная аутентификация выключена.</p>
      <button v-if="step === 'idle'" class="primary-btn" @click="startEnroll">Включить 2FA</button>

      <div v-if="step === 'enrolling'" class="enroll-block">
        <p>Отсканируйте секрет в приложении-аутентификаторе (Google Authenticator, Authy и т.п.):</p>
        <code class="secret">{{ secret }}</code>
        <p class="uri">{{ provisioningUri }}</p>
        <label>
          Код из приложения
          <input v-model="code" type="text" inputmode="numeric" maxlength="6" />
        </label>
        <button class="primary-btn" @click="confirmEnable">Подтвердить и включить</button>
      </div>

      <div v-if="step === 'enabled-once'" class="recovery-block">
        <p>2FA включена. Сохраните резервные коды — они показываются один раз:</p>
        <ul class="recovery-codes">
          <li v-for="c in recoveryCodes" :key="c">{{ c }}</li>
        </ul>
      </div>
    </template>

    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<style scoped>
.mfa {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  max-width: 420px;
}
.status {
  font-size: 0.9rem;
  color: #475569;
}
.status.enabled {
  color: #16a34a;
}
label {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #334155;
}
input {
  padding: 0.5rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
}
.secret {
  display: block;
  background: #f1f5f9;
  padding: 0.5rem;
  border-radius: 6px;
  font-size: 0.9rem;
  word-break: break-all;
}
.uri {
  font-size: 0.75rem;
  color: #94a3b8;
  word-break: break-all;
}
.recovery-codes {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.4rem;
  font-family: monospace;
  background: #f8fafc;
  padding: 0.75rem 1rem;
  border-radius: 8px;
}
.primary-btn,
.danger-btn {
  align-self: flex-start;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
.primary-btn {
  background: #2563eb;
  color: #fff;
}
.danger-btn {
  background: #fee2e2;
  color: #dc2626;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
}
</style>
