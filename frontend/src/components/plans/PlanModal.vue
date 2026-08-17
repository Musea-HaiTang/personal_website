<script setup>
import { reactive, watch } from 'vue'

import BaseModal from '../BaseModal.vue'

const props = defineProps({
  plan: { type: Object, default: null }
})
const emit = defineEmits(['save', 'close'])

const form = reactive({ title: '', importance: 2, note: '' })

watch(
  () => props.plan,
  (plan) => {
    form.title = plan?.title || ''
    form.importance = plan?.importance ?? 2
    form.note = plan?.note || ''
  },
  { immediate: true }
)

function submit() {
  emit('save', {
    title: form.title.trim(),
    importance: Number(form.importance),
    note: form.note.trim() || null
  })
}
</script>

<template>
  <BaseModal @close="emit('close')">
    <div class="w-full max-w-md rounded-xl bg-card p-6 shadow-xl">
      <h3 class="mb-4 text-lg font-semibold">{{ plan?.id ? '编辑计划' : '添加本周计划' }}</h3>
      <form @submit.prevent="submit">
        <label class="mb-1 block text-sm text-sub">计划名称</label>
        <input v-model="form.title" type="text" required class="mb-3 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" />
        <label class="mb-1 block text-sm text-sub">重要度</label>
        <select v-model="form.importance" class="mb-3 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none">
          <option :value="1">低</option>
          <option :value="2">中</option>
          <option :value="3">高</option>
        </select>
        <label class="mb-1 block text-sm text-sub">备注（可选）</label>
        <textarea v-model="form.note" rows="2" class="mb-4 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none"></textarea>
        <div class="flex justify-end gap-2">
          <button type="button" class="rounded-lg border border-hairline px-4 py-2 text-sm" @click="emit('close')">取消</button>
          <button type="submit" class="rounded-lg bg-teal px-4 py-2 text-sm font-semibold text-white hover:bg-teal-dark">保存</button>
        </div>
      </form>
    </div>
  </BaseModal>
</template>
