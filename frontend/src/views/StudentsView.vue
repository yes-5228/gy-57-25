<template>
  <section class="view">
    <header class="view-header">
      <div>
        <p class="eyebrow">Student</p>
        <h2>学员管理</h2>
      </div>
      <div class="filter-row">
        <label class="filter-label">
          按标签筛选：
          <select v-model="filterTag" class="filter-select">
            <option value="">全部学员</option>
            <option v-for="def in tagDefinitions" :key="def.key" :value="def.value">
              {{ def.value }}
            </option>
          </select>
        </label>
      </div>
    </header>

    <div class="split">
      <form class="panel form" @submit.prevent="submit">
        <h3>新增学员</h3>
        <label>姓名<input v-model="form.name" required /></label>
        <label>电话<input v-model="form.phone" required /></label>
        <label>剩余课时<input v-model.number="form.remaining_hours" type="number" min="0" required /></label>
        <div class="tags-field">
          <label class="tags-label">学员标签</label>
          <div class="tag-options">
            <label
              v-for="def in tagDefinitions"
              :key="def.key"
              class="tag-option"
              :title="def.hint"
            >
              <input
                type="checkbox"
                :value="def.value"
                v-model="form.tags"
              />
              <TagBadge :tag="def.value" />
            </label>
          </div>
          <small class="hint-text">提示：标签会影响预约时的提示和规则</small>
        </div>
        <button class="primary" type="submit">
          <UserPlus :size="18" />
          保存学员
        </button>
        <p v-if="message" class="message">{{ message }}</p>
      </form>

      <section class="panel list-panel">
        <h3>学员列表</h3>
        <table>
          <thead>
            <tr>
              <th>姓名</th>
              <th>电话</th>
              <th>剩余课时</th>
              <th>标签</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="student in filteredStudents" :key="student.id">
              <td>{{ student.name }}</td>
              <td>{{ student.phone }}</td>
              <td>
                <span :class="{ 'low-hours': student.remaining_hours <= 5 }">
                  {{ student.remaining_hours }}h
                </span>
              </td>
              <td>
                <div class="cell-tags">
                  <TagBadge v-for="tag in student.tags" :key="tag" :tag="tag" />
                  <span v-if="!student.tags || student.tags.length === 0" class="empty-tags">无</span>
                </div>
              </td>
              <td>
                <button class="ghost" @click="openTagEditor(student)">
                  <Pencil :size="14" />
                  编辑标签
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

    <div v-if="editingStudent" class="modal-overlay" @click.self="editingStudent = null">
      <div class="modal">
        <div class="modal-header">
          <h3>编辑学员标签 - {{ editingStudent.name }}</h3>
          <button class="close-btn" @click="editingStudent = null">
            <X :size="18" />
          </button>
        </div>
        <div class="modal-body">
          <div class="tag-options">
            <label
              v-for="def in tagDefinitions"
              :key="def.key"
              class="tag-option"
              :title="def.hint"
            >
              <input
                type="checkbox"
                :value="def.value"
                v-model="editTags"
              />
              <TagBadge :tag="def.value" />
            </label>
          </div>
          <div v-if="hintForSelectedTags.length > 0" class="hints-area">
            <p class="hints-title">选中标签的预约提示：</p>
            <HintAlert
              v-for="(hint, idx) in hintForSelectedTags"
              :key="idx"
              :message="hint.message"
              :level="hint.level"
              :tag="hint.tag"
            />
          </div>
        </div>
        <div class="modal-footer">
          <button class="ghost" @click="editingStudent = null">取消</button>
          <button class="primary" @click="saveTags">
            <Check :size="16" />
            保存
          </button>
        </div>
        <p v-if="editMessage" class="edit-message">{{ editMessage }}</p>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { UserPlus, Pencil, X, Check } from 'lucide-vue-next'
import { studentApi } from '../api/modules'
import TagBadge from '../components/TagBadge.vue'
import HintAlert from '../components/HintAlert.vue'

const props = defineProps({
  students: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['changed'])
const message = ref('')
const editMessage = ref('')
const tagDefinitions = ref([])
const filterTag = ref('')
const editingStudent = ref(null)
const editTags = ref([])

const form = reactive({
  name: '',
  phone: '',
  remaining_hours: 20,
  tags: [],
})

const filteredStudents = computed(() => {
  if (!filterTag.value) return props.students
  return props.students.filter((s) => (s.tags || []).includes(filterTag.value))
})

const hintForSelectedTags = computed(() => {
  const hints = []
  const tagHints = {
    '新手': { message: '该学员为新手，建议安排耐心细致的教练，初次预约请预留充足时间', level: 'warning' },
    '补考': { message: '该学员需要补考，建议重点辅导薄弱环节，预约时优先安排经验丰富的教练', level: 'warning' },
    '重点跟进': { message: '该学员需要重点跟进，建议教练提前了解学员学习进度，课后及时反馈', level: 'warning' },
    '学习快': { message: '该学员学习进度较快，可适当加快教学节奏', level: 'info' },
    '需多加练习': { message: '该学员需要多加练习，建议教练耐心指导，合理安排课时进度', level: 'info' },
  }
  for (const tag of editTags.value) {
    const hint = tagHints[tag]
    if (hint) {
      hints.push({ ...hint, tag })
    }
  }
  return hints
})

async function loadTagDefinitions() {
  tagDefinitions.value = await studentApi.listTagDefinitions()
}

function openTagEditor(student) {
  editingStudent.value = student
  editTags.value = [...(student.tags || [])]
  editMessage.value = ''
}

async function saveTags() {
  try {
    await studentApi.updateTags(editingStudent.value.id, editTags.value)
    editMessage.value = '标签已更新'
    emit('changed')
    setTimeout(() => {
      editingStudent.value = null
    }, 800)
  } catch (error) {
    editMessage.value = error.message
  }
}

async function submit() {
  message.value = ''
  try {
    await studentApi.create({
      name: form.name,
      phone: form.phone,
      remaining_hours: form.remaining_hours,
      tags: form.tags,
    })
    form.name = ''
    form.phone = ''
    form.remaining_hours = 20
    form.tags = []
    message.value = '学员已创建'
    emit('changed')
  } catch (error) {
    message.value = error.message
  }
}

onMounted(loadTagDefinitions)
watch(() => props.students, () => {
  if (editingStudent.value) {
    const updated = props.students.find((s) => s.id === editingStudent.value.id)
    if (updated) editingStudent.value = updated
  }
})
</script>

<style scoped>
.filter-row {
  display: flex;
  align-items: center;
}

.filter-label {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #52616b;
}

.filter-select {
  width: auto;
  min-width: 140px;
}

.tags-field {
  display: grid;
  gap: 8px;
}

.tags-label {
  color: #334e68;
  font-size: 14px;
  font-weight: 500;
}

.tag-options {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-option {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.15s;
}

.tag-option:hover {
  background: #f0f4f8;
}

.tag-option input[type="checkbox"] {
  width: 16px;
  height: 16px;
  min-height: unset;
  cursor: pointer;
}

.hint-text {
  color: #627d98;
  font-size: 12px;
}

.cell-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.empty-tags {
  color: #9fb3c8;
  font-size: 13px;
}

.low-hours {
  color: #b42318;
  font-weight: 600;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
}

.modal {
  background: #fff;
  border-radius: 12px;
  width: 100%;
  max-width: 520px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid #e4e7eb;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: transparent;
  border: 0;
  border-radius: 6px;
  padding: 6px;
  color: #627d98;
  cursor: pointer;
  line-height: 1;
}

.close-btn:hover {
  background: #edf2f7;
  color: #1f2933;
}

.modal-body {
  padding: 20px 22px;
  overflow-y: auto;
  display: grid;
  gap: 18px;
}

.hints-area {
  display: grid;
  gap: 10px;
  padding-top: 8px;
  border-top: 1px dashed #d9e2ec;
}

.hints-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #334e68;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 22px;
  border-top: 1px solid #e4e7eb;
}

.edit-message {
  margin: 0;
  padding: 0 22px 18px;
  color: #0f766e;
}
</style>
