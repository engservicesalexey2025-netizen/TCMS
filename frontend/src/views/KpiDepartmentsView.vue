<script setup>
import { ref } from "vue";

// Заготовка страницы — расчёт по загруженным эксель-файлам будет добавлен
// позже (логика ещё уточняется), сейчас только сама страница и выбор файла.
const pendingFile = ref(null);

function handleFileChange(event) {
  pendingFile.value = event.target.files[0] || null;
}
</script>

<template>
  <div class="kpi-departments-view">
    <h2>KPI ТН Подразделения</h2>
    <p class="intro">
      Расчёт KPI по подразделениям на основе загруженных эксель-файлов — логика расчёта будет
      добавлена позже. Пока доступна только загрузка файла.
    </p>

    <section class="card">
      <label class="file-btn">
        {{ pendingFile ? pendingFile.name : "Выбрать эксель-файл" }}
        <input type="file" accept=".xlsx" @change="handleFileChange" hidden />
      </label>
      <p class="placeholder-hint">Расчёт будет добавлен позже.</p>
    </section>
  </div>
</template>

<style scoped>
.kpi-departments-view h2 {
  margin: 0 0 0.5rem;
}
.intro {
  color: #64748b;
  font-size: 0.9rem;
  max-width: 60rem;
  margin: 0 0 1.25rem;
}
.card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.5rem;
}
.file-btn {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.85rem;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #334155;
}
.placeholder-hint {
  margin: 1rem 0 0;
  color: #94a3b8;
  font-size: 0.85rem;
}
</style>
