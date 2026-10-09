<script setup>
import { computed, reactive, ref, watch } from "vue";
import apiClient from "../api/client";
import EmployeePickerModal from "./EmployeePickerModal.vue";
import { useAuthStore } from "../stores/auth";

const props = defineProps({
  unitId: { type: String, required: true },
  allUnits: { type: Array, required: true }, // плоский список всех активных единиц — для выбора родителя
});
const emit = defineEmits(["changed", "select", "deleted"]);

const auth = useAuthStore();
const canWrite = computed(() => auth.can("ORG_UNITS", "UPDATE"));
const canCreate = computed(() => auth.can("ORG_UNITS", "CREATE"));
const canDelete = computed(() => auth.can("ORG_UNITS", "DELETE"));

const TYPE_LABELS = {
  DIVISION: "Дивизион",
  CITY: "Город",
  DEPARTMENT: "Управление",
  GROUP: "Группа",
};
// Название должности руководителя меняется по уровню, хотя механизм
// назначения (ManagerEmployeeId) у всех уровней один и тот же.
const MANAGER_LABELS = {
  DIVISION: "Руководитель дивизиона",
  CITY: "Директор филиала",
  DEPARTMENT: "Руководитель управления",
  GROUP: "Руководитель группы",
};
const unit = ref(null);
const managerLabel = computed(() => MANAGER_LABELS[unit.value?.UnitType] || "Руководитель");
const typeOptions = Object.entries(TYPE_LABELS).map(([value, label]) => ({ value, label }));
const form = reactive({ Name: "", UnitType: "DIVISION", Code: "", ParentOrgUnitId: null, Comment: "" });
const saving = ref(false);
const saveError = ref("");

const managerPickerVisible = ref(false);
const employeePickerVisible = ref(false);

// Жёсткий маршрут иерархии (тот же список, что и в backend-валидации
// app/api/v1/org.py::ORG_UNIT_ALLOWED_PARENT_TYPES) — выбор родителя всегда
// предлагает только допустимый уровень, а не любое подразделение подряд.
const ALLOWED_PARENT_TYPES = {
  DIVISION: [],
  CITY: ["DIVISION"],
  DEPARTMENT: ["CITY"],
  GROUP: ["DEPARTMENT"],
};

const parentOptions = computed(() => {
  const allowed = ALLOWED_PARENT_TYPES[form.UnitType] || [];
  return props.allUnits
    .filter((u) => u.Id !== props.unitId && allowed.includes(u.UnitType))
    .map((u) => ({ value: u.Id, label: u.Name }));
});

// Следующий уровень цепочки — кнопка "+ Добавить X" в карточке сразу
// создаёт нужный тип с уже проставленным родителем (текущий узел), без
// ручного выбора типа/родителя в общей форме.
const CHILD_TYPE = { DIVISION: "CITY", CITY: "DEPARTMENT", DEPARTMENT: "GROUP", GROUP: null };
const CHILD_BUTTON_LABEL = {
  DIVISION: "+ Добавить город",
  CITY: "+ Добавить управление",
  DEPARTMENT: "+ Добавить группу",
};
const childType = computed(() => CHILD_TYPE[unit.value?.UnitType] || null);
const addChildVisible = ref(false);
const addChildForm = reactive({ Name: "", Code: "" });
const addChildError = ref("");

async function submitAddChild() {
  addChildError.value = "";
  try {
    const { data } = await apiClient.post("/org-units", {
      Name: addChildForm.Name,
      UnitType: childType.value,
      Code: addChildForm.Code || null,
      ParentOrgUnitId: props.unitId,
    });
    addChildVisible.value = false;
    Object.assign(addChildForm, { Name: "", Code: "" });
    await load();
    emit("changed");
    emit("select", data.Id);
  } catch (e) {
    addChildError.value = e.response?.data?.detail || "Ошибка создания";
  }
}

async function deleteUnit() {
  if (!window.confirm(`Отправить «${unit.value.Name}» в архив?`)) return;
  await apiClient.post(`/org-units/${props.unitId}/archive`);
  emit("changed");
  emit("deleted");
}

// Смена типа пользователем (а не первичная загрузка формы) — редкая
// осознанная реорганизация: прежний родитель почти наверняка не подходит
// новому уровню, поэтому просим выбрать заново. Вешаем на @change самого
// select'а (см. template), а не на watch(form.UnitType) — иначе load()
// сбрасывал бы уже корректно загруженный ParentOrgUnitId при каждом
// открытии карточки.
function onTypeChanged() {
  form.ParentOrgUnitId = null;
}

async function load() {
  const { data } = await apiClient.get(`/org-units/${props.unitId}/detail`);
  unit.value = data;
  Object.assign(form, {
    Name: data.Name,
    UnitType: data.UnitType,
    Code: data.Code || "",
    ParentOrgUnitId: data.ParentOrgUnitId,
    Comment: data.Comment || "",
  });
}

watch(() => props.unitId, load, { immediate: true });

async function save() {
  saveError.value = "";
  saving.value = true;
  try {
    await apiClient.patch(`/org-units/${props.unitId}`, {
      Name: form.Name,
      UnitType: form.UnitType,
      Code: form.Code || null,
      ParentOrgUnitId: form.ParentOrgUnitId,
      Comment: form.Comment || null,
    });
    await load();
    emit("changed");
  } catch (e) {
    saveError.value = e.response?.data?.detail || "Ошибка сохранения";
  } finally {
    saving.value = false;
  }
}

async function setManager(employeeId) {
  try {
    await apiClient.post(`/org-units/${props.unitId}/set-manager`, { EmployeeId: employeeId });
  } catch (e) {
    const detail = e.response?.data?.detail;
    if (e.response?.status === 409 && detail?.conflict) {
      if (!window.confirm(detail.message)) return;
      await apiClient.post(`/org-units/${props.unitId}/set-manager`, {
        EmployeeId: employeeId,
        Force: true,
      });
    } else {
      throw e;
    }
  }
  managerPickerVisible.value = false;
  await load();
  emit("changed");
}

async function assignEmployee(employeeId) {
  await apiClient.post(`/org-units/${props.unitId}/assign-employee`, { EmployeeId: employeeId });
  employeePickerVisible.value = false;
  await load();
  emit("changed");
}

async function removeEmployee(employeeId) {
  await apiClient.post(`/org-units/${props.unitId}/remove-employee`, { EmployeeId: employeeId });
  await load();
  emit("changed");
}
</script>

<template>
  <div v-if="unit" class="card">
    <div class="section">
      <h3>Основная информация</h3>
      <div class="form-grid">
        <label class="field">
          Название
          <input v-model="form.Name" type="text" :disabled="!canWrite" />
        </label>
        <label class="field">
          Тип
          <select v-model="form.UnitType" :disabled="!canWrite" @change="onTypeChanged">
            <option v-for="o in typeOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
          </select>
        </label>
        <label class="field">
          Код
          <input v-model="form.Code" type="text" :disabled="!canWrite" />
        </label>
        <label class="field wide">
          Комментарий
          <input v-model="form.Comment" type="text" :disabled="!canWrite" />
        </label>
      </div>
      <p v-if="saveError" class="error">{{ saveError }}</p>
      <div class="actions-row">
        <button v-if="canWrite" class="primary-btn" :disabled="saving" @click="save">
          {{ saving ? "Сохранение..." : "Сохранить" }}
        </button>
        <button v-if="canDelete" class="link-btn danger" @click="deleteUnit">
          Удалить
        </button>
      </div>
    </div>

    <div class="section">
      <h3>{{ managerLabel }}</h3>
      <div class="manager-row">
        <span>{{ unit.ManagerName || "Не назначен" }}</span>
        <button v-if="canWrite" class="secondary-btn" @click="managerPickerVisible = true">
          {{ unit.ManagerName ? "Изменить" : "Назначить" }}
        </button>
        <button v-if="canWrite && unit.ManagerName" class="link-btn" @click="setManager(null)">
          Снять
        </button>
      </div>
    </div>

    <div class="section">
      <h3>Родительское подразделение</h3>
      <span v-if="form.UnitType === 'DIVISION'" class="readonly-value">
        — нет, Дивизион — верхний уровень —
      </span>
      <select v-else v-model="form.ParentOrgUnitId" :disabled="!canWrite" @change="save">
        <option :value="null" disabled>— выберите —</option>
        <option v-for="o in parentOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
      </select>
      <p v-if="unit.ParentName" class="hint">Сейчас: {{ unit.ParentName }}</p>
    </div>

    <div class="section" v-if="childType || unit.Children.length">
      <div class="section-header">
        <h3>Подчинённые подразделения</h3>
        <button
          v-if="canCreate && childType"
          class="secondary-btn"
          @click="addChildVisible = !addChildVisible"
        >
          {{ addChildVisible ? "Отмена" : CHILD_BUTTON_LABEL[unit.UnitType] }}
        </button>
      </div>
      <div v-if="addChildVisible" class="add-child-form">
        <label class="field">
          Название
          <input v-model="addChildForm.Name" type="text" />
        </label>
        <label class="field">
          Код
          <input v-model="addChildForm.Code" type="text" />
        </label>
        <button class="primary-btn" @click="submitAddChild">Создать</button>
        <p v-if="addChildError" class="error">{{ addChildError }}</p>
      </div>
      <ul v-if="unit.Children.length" class="children-list">
        <li v-for="c in unit.Children" :key="c.Id">
          <button class="link-btn" @click="emit('select', c.Id)">{{ c.Name }}</button>
        </li>
      </ul>
      <p v-else class="empty">Пока нет ни одного подразделения этого уровня</p>
    </div>

    <div class="section">
      <div class="section-header">
        <h3>Сотрудники подразделения</h3>
        <button
          v-if="canWrite && unit.UnitType === 'GROUP'"
          class="secondary-btn"
          @click="employeePickerVisible = true"
        >
          + Добавить сотрудника
        </button>
      </div>
      <p v-if="unit.UnitType !== 'GROUP'" class="hint">
        Сотрудники закрепляются только за «Группой» — нижним уровнем иерархии.
      </p>
      <table v-if="unit.Employees.length" class="grid">
        <thead>
          <tr>
            <th>ФИО</th>
            <th>Должность</th>
            <th>Статус</th>
            <th v-if="canWrite"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in unit.Employees" :key="e.Id">
            <td>{{ e.FullName }}</td>
            <td>{{ e.PositionName || "—" }}</td>
            <td>{{ e.Status }}</td>
            <td v-if="canWrite">
              <button class="link-btn danger" @click="removeEmployee(e.Id)">Убрать</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-else class="empty">В подразделении пока нет сотрудников</p>
    </div>

    <EmployeePickerModal
      :visible="managerPickerVisible"
      title="Назначить руководителя"
      @select="setManager"
      @close="managerPickerVisible = false"
    />
    <EmployeePickerModal
      :visible="employeePickerVisible"
      title="Добавить сотрудника"
      :exclude-ids="unit.Employees.map((e) => e.Id)"
      @select="assignEmployee"
      @close="employeePickerVisible = false"
    />
  </div>
</template>

<style scoped>
.card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
.section h3 {
  margin: 0 0 0.75rem;
  font-size: 0.95rem;
  color: #1e2b3a;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}
.section-header h3 {
  margin: 0;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}
.field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.85rem;
  color: #334155;
}
.field.wide {
  grid-column: 1 / -1;
}
.field input,
select {
  padding: 0.5rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
}
.readonly-value {
  padding: 0.5rem 0;
  color: #64748b;
}
.manager-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
}
.hint {
  margin: 0.4rem 0 0;
  font-size: 0.8rem;
  color: #64748b;
}
.children-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.actions-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 1rem;
}
.add-child-form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.75rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 0.75rem;
  margin-bottom: 0.75rem;
}
.primary-btn {
  margin-top: 1rem;
  padding: 0.5rem 1.1rem;
  border: none;
  border-radius: 6px;
  background: #2563eb;
  color: #fff;
  cursor: pointer;
  font-size: 0.85rem;
}
.secondary-btn {
  padding: 0.4rem 0.8rem;
  border: 1px solid #2563eb;
  border-radius: 6px;
  background: #fff;
  color: #2563eb;
  cursor: pointer;
  font-size: 0.8rem;
}
.link-btn {
  border: none;
  background: none;
  color: #2563eb;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0;
}
.link-btn.danger {
  color: #dc2626;
}
.error {
  color: #dc2626;
  font-size: 0.85rem;
  margin-top: 0.5rem;
}
.grid {
  width: 100%;
  border-collapse: collapse;
}
.grid th,
.grid td {
  text-align: left;
  padding: 0.5rem 0.6rem;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.85rem;
}
.empty {
  color: #94a3b8;
  font-size: 0.85rem;
}
</style>
