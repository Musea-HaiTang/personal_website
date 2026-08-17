<script setup>
import { reactive, watch } from 'vue'

import BaseModal from '../BaseModal.vue'

const props = defineProps({
  task: { type: Object, default: null }
})
const emit = defineEmits(['confirm', 'close'])

const form = reactive({ note: '' })

watch(
  () => props.task,
  (task) => {
    form.note = task?.review_note || ''
  },
  { immediate: true }
)

function submit() {
  emit('confirm', form.note.trim())
}
</script>

<template>
  <BaseModal @close="emit('close')">
    <div class="w-full max-w-md rounded-xl bg-card p-6 shadow-xl">
      <h3 class="mb-4 text-lg font-semibold">计划复盘</h3>
      <p class="mb-1 text-sm text-sub">任务</p>
      <p class="mb-4 rounded-lg border border-hairline bg-paper-soft px-3 py-2 text-sm font-semibold text-ink">{{ task?.title }}</p>
      <label class="mb-1 block text-sm text-sub">说明（可选）</label>
      <textarea v-model="form.note" rows="3" class="mb-4 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="写下为什么没完成，方便之后复盘…"></textarea>
      <div class="flex justify-end gap-2">
        <button class="rounded-lg border border-hairline px-4 py-2 text-sm" @click="emit('close')">取消</button>
        <button class="rounded-lg bg-teal px-4 py-2 text-sm font-semibold text-white hover:bg-teal-dark" @click="submit">顺延到明天</button>
      </div>
    </div>
  </BaseModal>
</template>
