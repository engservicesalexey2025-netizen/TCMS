<script setup>
import { onMounted, ref, watch } from "vue";
import apiClient from "../api/client";

const props = defineProps({
  visible: { type: Boolean, default: false },
  title: { type: String, default: "Выбрать сотрудника" },
  // Исключаем сотрудников, которые и так уже в текущем подразделении —
  // иначе «Добавить сотрудника» предложит того, кто там уже числится.
  excludeIds: { type: Array, default: () => [] },
});
const emit = defineEmits(["select", "close"]);

const search = ref("");
const employees = ref([]);
const positions = ref([]);
const loading = ref(false);
let searchTimer = null;

function labelFor(options, id) {
  return options.find((o) => o.Id === id)?.Name ?? "—";
}

async function loadPositions() {
  if (positions.value.length) return;
  const { data } = await apiClient.get("/positions", { params: { limit: 500 } });
  positions.value = data.items;
}

async function search_() {
  loading.value = true;
  try {
    const { data } = await apiClient.get("/employees", {
      params: { search: search.value || undefined, limit: 50 },
    });
    employees.value = data.items.filter((e) => !props.excludeIds.includes(e.Id));
  } finally {
    loading.value = false;
  }
}

watch(search, () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(search_, 250);
});

watch(
  () => props.visible,
  (visible) => {
    if (visible) {
      search.value = "";
      loadPositions();
      search_();
    }
  },
);

onMounted(() => {
  if (props.visible) {
    loadPositions();
    search_();
  }
});

function pick(employee) {
  emit("select", employee.Id, employee);
}
</script>

<template>
  <div v-if="visible" class="overlay" @click.self="emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h3>{{ title }}</h3>
        <button class="close-btn" @click="emit('close')">×</button>
      </div>
      <input
        v-model="search"
        type="text"
        class="search-input"
        placeholder="Поиск по ФИО..."
        autofocus
      />
      <div class="list">
        <div v-if="loading" class="empty">Загрузка...</div>
        <div v-else-if="employees.length === 0" class="empty">Ничего не найдено</div>
        <div v-for="e in employees" :key="e.Id" class="row">
          <div class="info">
            <div class="name">{{ e.FullName }}</div>
            <div class="position">{{ labelFor(positions, e.PositionId) }}</div>
          </div>
          <button class="pick-btn" @click="pick(e)">Выбрать</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.modal {
  background: #fff;
  border-radius: 10px;
  padding: 1.25rem;
  width: 420px;
  max-height: 70vh;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.modal-header h3 {
  margin: 0;
  font-size: 1rem;
}
.close-btn {
  border: none;
  background: none;
  font-size: 1.3rem;
  line-height: 1;
  cursor: pointer;
  color: #64748b;
}
.search-input {
  padding: 0.5rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
}
.list {
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}
.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.6rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
}
.name {
  font-size: 0.9rem;
  color: #1e2b3a;
}
.position {
  font-size: 0.8rem;
  color: #64748b;
}
.pick-btn {
  border: none;
  background: #2563eb;
  color: #fff;
  border-radius: 6px;
  padding: 0.35rem 0.75rem;
  font-size: 0.8rem;
  cursor: pointer;
}
.empty {
  text-align: center;
  color: #94a3b8;
  padding: 1.5rem 0;
  font-size: 0.85rem;
}
</style>
