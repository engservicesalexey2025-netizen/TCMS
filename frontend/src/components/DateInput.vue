<script setup>
import { ref, watch } from "vue";
import { displayDateToIso, isoToDisplayDate } from "../utils/date";

const props = defineProps({
  modelValue: { type: String, default: null }, // ISO "YYYY-MM-DD" (или null)
  disabled: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue", "blur"]);

const text = ref(isoToDisplayDate(props.modelValue));
watch(
  () => props.modelValue,
  (v) => {
    text.value = isoToDisplayDate(v);
  },
);

function handleInput(event) {
  const digits = event.target.value.replace(/\D/g, "").slice(0, 8);
  let out = digits.slice(0, 2);
  if (digits.length > 2) out += "." + digits.slice(2, 4);
  if (digits.length > 4) out += "." + digits.slice(4, 8);
  text.value = out;

  if (out === "") {
    emit("update:modelValue", null);
    return;
  }
  const iso = displayDateToIso(out);
  if (iso) emit("update:modelValue", iso);
}
</script>

<template>
  <input
    type="text"
    inputmode="numeric"
    :value="text"
    :disabled="disabled"
    placeholder="ДД.ММ.ГГГГ"
    maxlength="10"
    @input="handleInput"
    @blur="emit('blur')"
  />
</template>

<style scoped>
input {
  width: 100%;
  padding: 0.5rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
  box-sizing: border-box;
}
</style>
