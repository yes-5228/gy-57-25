<template>
  <section class="view">
    <header class="view-header">
      <div>
        <p class="eyebrow">Booking</p>
        <h2>练车预约</h2>
      </div>
    </header>

    <div class="split">
      <form class="panel form" @submit.prevent="submit">
        <h3>新建预约</h3>
        <label>
          学员
          <select v-model.number="form.student_id" required @change="onStudentChange">
            <option value="" disabled>选择学员</option>
            <option v-for="student in students" :key="student.id" :value="student.id">
              {{ student.name }}（剩余 {{ student.remaining_hours }}h）
              <span v-if="student.tags && student.tags.length">
                [{{ student.tags.join('、') }}]
              </span>
            </option>
          </select>
        </label>
        <label>
          教练
          <select v-model.number="form.coach_id" required>
            <option value="" disabled>选择教练</option>
            <option v-for="coach in activeCoaches" :key="coach.id" :value="coach.id">
              {{ coach.name }} - {{ coach.car_no }}
            </option>
          </select>
        </label>
        <label>
          开始时间
          <input v-model="form.start_time" type="datetime-local" required />
        </label>
        <label>
          结束时间
          <input v-model="form.end_time" type="datetime-local" required />
        </label>

        <div v-if="hints.length > 0" class="hints-panel">
          <p class="hints-panel-title">
            <Lightbulb :size="16" />
            学员注意事项
          </p>
          <div class="hints-list">
            <HintAlert
              v-for="(hint, idx) in hints"
              :key="idx"
              :message="hint.message"
              :level="hint.level"
              :tag="hint.tag"
            />
          </div>
        </div>

        <button class="primary" type="submit">
          <CalendarCheck :size="18" />
          提交预约
        </button>
        <p v-if="message" class="message" :class="{ 'error': isErrorMessage }">{{ message }}</p>
      </form>

      <section class="panel list-panel">
        <h3>预约列表</h3>
        <EmptyState v-if="appointments.length === 0" />
        <table v-else>
          <thead>
            <tr>
              <th>时间</th>
              <th>学员</th>
              <th>教练</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in appointments" :key="item.id">
              <td>{{ formatDateTime(item.start_time) }} - {{ formatDateTime(item.end_time) }}</td>
              <td>
                <div class="student-cell">
                  <span class="student-name">{{ item.student_name }}</span>
                  <div v-if="item.student_tags && item.student_tags.length" class="student-cell-tags">
                    <TagBadge v-for="tag in item.student_tags" :key="tag" :tag="tag" />
                  </div>
                </div>
              </td>
              <td>{{ item.coach_name }}</td>
              <td><StatusBadge :status="item.status" /></td>
              <td>
                <button
                  class="ghost danger"
                  :disabled="item.status !== 'booked'"
                  @click="cancel(item.id)"
                >
                  <XCircle :size="16" />
                  取消
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>
    </div>

    <div v-if="selectedAppointment" class="modal-overlay" @click.self="selectedAppointment = null">
      <div class="modal">
        <div class="modal-header">
          <h3>预约详情</h3>
          <button class="close-btn" @click="selectedAppointment = null">
            <X :size="18" />
          </button>
        </div>
        <div class="modal-body">
          <div class="detail-row">
            <span class="detail-label">学员</span>
            <span class="detail-value">{{ selectedAppointment.student_name }}</span>
          </div>
          <div v-if="selectedAppointment.student_tags && selectedAppointment.student_tags.length" class="detail-row">
            <span class="detail-label">学员标签</span>
            <div class="detail-tags">
              <TagBadge v-for="tag in selectedAppointment.student_tags" :key="tag" :tag="tag" />
            </div>
          </div>
          <div class="detail-row">
            <span class="detail-label">教练</span>
            <span class="detail-value">{{ selectedAppointment.coach_name }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">时间</span>
            <span class="detail-value">
              {{ formatDateTime(selectedAppointment.start_time) }} - {{ formatDateTime(selectedAppointment.end_time) }}
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">状态</span>
            <StatusBadge :status="selectedAppointment.status" />
          </div>

          <div v-if="selectedAppointment.hints && selectedAppointment.hints.length" class="detail-hints">
            <p class="detail-hints-title">
              <Lightbulb :size="16" />
              提示信息
            </p>
            <div class="hints-list">
              <HintAlert
                v-for="(hint, idx) in selectedAppointment.hints"
                :key="idx"
                :message="hint.message"
                :level="hint.level"
                :tag="hint.tag"
              />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="primary" @click="selectedAppointment = null">关闭</button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { CalendarCheck, XCircle, X, Lightbulb } from 'lucide-vue-next'
import EmptyState from '../components/EmptyState.vue'
import StatusBadge from '../components/StatusBadge.vue'
import TagBadge from '../components/TagBadge.vue'
import HintAlert from '../components/HintAlert.vue'
import { appointmentApi, studentApi } from '../api/modules'
import { addHours, formatDateTime, toLocalInputValue } from '../utils/date'

const props = defineProps({
  students: {
    type: Array,
    default: () => [],
  },
  coaches: {
    type: Array,
    default: () => [],
  },
  refreshToken: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['changed'])

const appointments = ref([])
const message = ref('')
const isErrorMessage = ref(false)
const hints = ref([])
const selectedAppointment = ref(null)
const initialStart = addHours(new Date(), 24)
const form = reactive({
  student_id: '',
  coach_id: '',
  start_time: toLocalInputValue(initialStart),
  end_time: toLocalInputValue(addHours(initialStart, 2)),
})

const activeCoaches = computed(() => props.coaches.filter((coach) => coach.active))

async function load() {
  appointments.value = await appointmentApi.list()
}

async function onStudentChange() {
  hints.value = []
  if (!form.student_id) return
  try {
    hints.value = await studentApi.getAppointmentHints(form.student_id)
  } catch (e) {
    hints.value = []
  }
}

async function submit() {
  message.value = ''
  isErrorMessage.value = false
  try {
    await appointmentApi.create({
      ...form,
      start_time: new Date(form.start_time).toISOString(),
      end_time: new Date(form.end_time).toISOString(),
    })
    message.value = '预约已创建'
    await load()
    emit('changed')
  } catch (error) {
    message.value = error.message
    isErrorMessage.value = true
  }
}

async function cancel(id) {
  message.value = ''
  isErrorMessage.value = false
  try {
    await appointmentApi.cancel(id, '前端操作取消')
    message.value = '预约已取消'
    await load()
    emit('changed')
  } catch (error) {
    message.value = error.message
    isErrorMessage.value = true
  }
}

onMounted(load)
watch(() => props.refreshToken, load)
</script>

<style scoped>
.hints-panel {
  display: grid;
  gap: 10px;
  padding: 14px;
  background: #f8fafc;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
}

.hints-panel-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #334e68;
}

.hints-list {
  display: grid;
  gap: 8px;
}

.message.error {
  color: #b42318;
}

.student-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.student-name {
  font-weight: 500;
}

.student-cell-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 3px;
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
  max-width: 560px;
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
  gap: 14px;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.detail-label {
  flex-shrink: 0;
  width: 80px;
  color: #627d98;
  font-size: 14px;
  padding-top: 2px;
}

.detail-value {
  flex: 1;
  color: #1f2933;
  font-size: 14px;
  font-weight: 500;
}

.detail-tags {
  flex: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.detail-hints {
  margin-top: 8px;
  padding-top: 14px;
  border-top: 1px dashed #d9e2ec;
  display: grid;
  gap: 10px;
}

.detail-hints-title {
  display: inline-flex;
  align-items: center;
  gap: 6px;
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
</style>
