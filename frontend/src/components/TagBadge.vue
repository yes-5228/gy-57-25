<template>
  <span
    class="tag-badge"
    :style="{ background: bgColor, color: textColor, borderColor: borderColor }"
  >
    {{ tag }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tag: {
    type: String,
    required: true,
  },
})

const TAG_COLORS = {
  '新手': '#3b82f6',
  '补考': '#ef4444',
  '重点跟进': '#f59e0b',
  '学习快': '#10b981',
  '需多加练习': '#8b5cf6',
}

const defaultColor = '#64748b'

const color = computed(() => TAG_COLORS[props.tag] || defaultColor)
const bgColor = computed(() => color.value + '15')
const textColor = computed(() => color.value)
const borderColor = computed(() => color.value + '40')
</script>

<style scoped>
.tag-badge {
  display: inline-flex;
  align-items: center;
  min-height: 24px;
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid;
  white-space: nowrap;
}
</style>
