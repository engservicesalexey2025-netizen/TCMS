<script setup>
defineProps({
  modelValue: { type: String, default: "" },
});
const emit = defineEmits(["update:modelValue"]);

function extractDigits(raw) {
  let digits = (raw || "").replace(/\D/g, "");
  // Only strip a leading country-code digit when a FULL 11-digit number was
  // pasted (e.g. "87011234567"/"77011234567") — a bare 10-digit subscriber
  // number legitimately starting with 7 (701, 707, 777...) must stay intact.
  if (digits.length === 11 && (digits.startsWith("7") || digits.startsWith("8"))) {
    digits = digits.slice(1);
  }
  return digits.slice(0, 10);
}

function formatPhone(digits) {
  if (!digits) return "";
  let out = "+7";
  out += ` (${digits.slice(0, 3)}`;
  if (digits.length >= 3) out += ")";
  if (digits.length > 3) out += `-${digits.slice(3, 6)}`;
  if (digits.length > 6) out += `-${digits.slice(6, 8)}`;
  if (digits.length > 8) out += `-${digits.slice(8, 10)}`;
  return out;
}

function handleInput(event) {
  const digits = extractDigits(event.target.value);
  emit("update:modelValue", formatPhone(digits));
}
</script>

<template>
  <input type="text" :value="modelValue" placeholder="+7 (___)-___-__-__" @input="handleInput" />
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
