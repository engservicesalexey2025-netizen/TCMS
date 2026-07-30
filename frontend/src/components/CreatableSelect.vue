<script setup>
import { computed, ref, watch } from "vue";
import apiClient from "../api/client";

const props = defineProps({
  modelValue: { type: [String, null], default: null },
  options: { type: Array, required: true }, // [{ label, value }]
  createEndpoint: { type: String, required: true }, // e.g. "/positions"
  placeholder: { type: String, default: "Выберите или введите..." },
  disabled: { type: Boolean, default: false },
});

const emit = defineEmits(["update:modelValue", "created", "deleted"]);

const query = ref("");
const open = ref(false);
const creating = ref(false);
const deletingId = ref(null);
const error = ref("");

function syncQueryFromValue() {
  const match = props.options.find((o) => o.value === props.modelValue);
  query.value = match ? match.label : "";
}

watch(() => props.modelValue, syncQueryFromValue, { immediate: true });
watch(() => props.options, syncQueryFromValue);

const filteredOptions = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return props.options;
  return props.options.filter((o) => o.label.toLowerCase().includes(q));
});

const exactMatch = computed(() =>
  props.options.some((o) => o.label.toLowerCase() === query.value.trim().toLowerCase()),
);
const showCreateOption = computed(
  () => query.value.trim().length > 0 && !exactMatch.value && !creating.value,
);

function select(opt) {
  emit("update:modelValue", opt.value);
  query.value = opt.label;
  open.value = false;
}

async function createNew() {
  const name = query.value.trim();
  if (!name || creating.value) return;
  creating.value = true;
  error.value = "";
  try {
    const { data } = await apiClient.post(props.createEndpoint, { Name: name });
    const newOption = { label: data.Name, value: data.Id };
    emit("created", newOption);
    emit("update:modelValue", newOption.value);
    query.value = newOption.label;
  } catch (e) {
    error.value = e.response?.data?.detail || "Не удалось создать значение";
  } finally {
    creating.value = false;
    open.value = false;
  }
}

function closeDelayed() {
  setTimeout(() => {
    open.value = false;
  }, 150);
}

function handleFocus() {
  if (!props.disabled) open.value = true;
}

async function removeOption(opt) {
  if (deletingId.value) return;
  if (!window.confirm(`Удалить значение «${opt.label}» из списка? Это действие затронет все места, где оно используется.`)) {
    return;
  }
  deletingId.value = opt.value;
  error.value = "";
  try {
    await apiClient.post(`${props.createEndpoint}/${opt.value}/archive`);
    emit("deleted", opt.value);
    if (props.modelValue === opt.value) {
      emit("update:modelValue", null);
      query.value = "";
    }
  } catch (e) {
    error.value = e.response?.data?.detail || "Не удалось удалить значение";
  } finally {
    deletingId.value = null;
  }
}
</script>

<template>
  <div class="creatable-select">
    <input
      v-model="query"
      type="text"
      :placeholder="placeholder"
      :disabled="disabled"
      @focus="handleFocus"
      @input="handleFocus"
      @blur="closeDelayed"
    />
    <ul v-if="open && !disabled" class="dropdown">
      <li v-for="opt in filteredOptions" :key="opt.value" class="option-row" @mousedown.prevent="select(opt)">
        <span class="option-label">{{ opt.label }}</span>
        <button
          type="button"
          class="delete-option-btn"
          title="Удалить значение из списка"
          :disabled="deletingId === opt.value"
          @mousedown.stop.prevent="removeOption(opt)"
        >
          ✗
        </button>
      </li>
      <li
        v-if="showCreateOption"
        class="create-option"
        @mousedown.prevent="createNew"
      >
        {{ creating ? "Создание..." : `+ Добавить «${query.trim()}»` }}
      </li>
      <li v-if="filteredOptions.length === 0 && !showCreateOption" class="empty-option">
        Ничего не найдено
      </li>
    </ul>
    <p v-if="error" class="error">{{ error }}</p>
  </div>
</template>

<style scoped>
.creatable-select {
  position: relative;
}
input {
  width: 100%;
  padding: 0.5rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
  box-sizing: border-box;
}
.dropdown {
  position: absolute;
  z-index: 20;
  top: calc(100% + 2px);
  left: 0;
  right: 0;
  max-height: 220px;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
  margin: 0;
  padding: 0.25rem 0;
  list-style: none;
}
.dropdown li {
  padding: 0.4rem 0.7rem;
  font-size: 0.85rem;
  cursor: pointer;
  color: #334155;
}
.dropdown li:hover {
  background: #f1f5f9;
}
.option-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}
.option-label {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.delete-option-btn {
  flex-shrink: 0;
  border: none;
  background: none;
  color: #f87171;
  cursor: pointer;
  font-size: 0.85rem;
  line-height: 1;
  padding: 0.1rem 0.3rem;
}
.delete-option-btn:hover {
  color: #dc2626;
}
.delete-option-btn:disabled {
  opacity: 0.4;
  cursor: default;
}
.create-option {
  color: #2563eb;
  font-weight: 500;
  border-top: 1px solid #e2e8f0;
}
.empty-option {
  color: #94a3b8;
  cursor: default;
}
.empty-option:hover {
  background: none;
}
.error {
  color: #dc2626;
  font-size: 0.8rem;
  margin: 0.25rem 0 0;
}
</style>
