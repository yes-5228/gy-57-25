<template>
  <div class="hint-alert" :class="`hint-${level}`">
    <div class="hint-icon">
      <Info v-if="level === 'info'" :size="18" />
      <AlertTriangle v-else-if="level === 'warning'" :size="18" />
      <AlertCircle v-else-if="level === 'danger'" :size="18" />
      <CheckCircle v-else :size="18" />
    </div>
    <div class="hint-content">
      <div class="hint-message">{{ message }}</div>
      <div v-if="tag" class="hint-tag">
        <TagBadge :tag="tag" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { Info, AlertTriangle, AlertCircle, CheckCircle } from 'lucide-vue-next'
import TagBadge from './TagBadge.vue'

defineProps({
  message: {
    type: String,
    required: true,
  },
  level: {
    type: String,
    default: 'info',
  },
  tag: {
    type: String,
    default: null,
  },
})
</script>

<style scoped>
.hint-alert {
  display: flex;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid;
}

.hint-icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.hint-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hint-message {
  font-size: 14px;
  line-height: 1.5;
}

.hint-tag {
  display: flex;
}

.hint-info {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1d4ed8;
}

.hint-info .hint-icon {
  color: #3b82f6;
}

.hint-warning {
  background: #fffbeb;
  border-color: #fde68a;
  color: #92400e;
}

.hint-warning .hint-icon {
  color: #f59e0b;
}

.hint-danger {
  background: #fef2f2;
  border-color: #fecaca;
  color: #991b1b;
}

.hint-danger .hint-icon {
  color: #ef4444;
}

.hint-success {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #166534;
}

.hint-success .hint-icon {
  color: #22c55e;
}
</style>
