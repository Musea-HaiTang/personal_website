<script setup>
import { computed, reactive, ref, watch } from 'vue'

import BaseModal from '../BaseModal.vue'

const props = defineProps({
  task: { type: Object, default: null },
  today: { type: String, default: '' },
  plans: { type: Array, default: () => [] }
})
const emit = defineEmits(['save', 'delete', 'close'])

const form = reactive({ title: '', importance: 2, date: '', note: '', planId: null, subtaskId: null })
const pickedSub = ref(null)

const pickableSubs = computed(() => {
  const plan = props.plans.find((p) => p.id === Number(form.planId))
  return plan ? plan.subtasks.filter((s) => !s.completed) : []
})

watch(
  () => props.task,
  (task) => {
    pickedSub.value = null
    form.title = task?.title || ''
    form.importance = task?.importance ?? 2
    form.date = task?.date || props.today
    form.note = task?.note || ''
    form.planId = task?.plan_id ?? null
    form.subtaskId = task?.subtask_id ?? null
  },
  { immediate: true }
)

function onPlanChange() {
  form.subtaskId = null
  pickedSub.value = null
}
function pickSubtask(sub) {
  pickedSub.value = sub
  form.subtaskId = sub.id
  form.title = sub.name
}
function submit() {
  const payload = {
    title: form.title.trim(),
    importance: Number(form.importance),
    date: form.date,
    note: form.note.trim() || null,
    plan_id: form.planId ? Number(form.planId) : null,
    subtask_id: form.subtaskId ? Number(form.subtaskId) : null
  }
  if (!payload.title || !payload.date) return
  emit('save', payload)
}
</script>

<template>
  <BaseModal @close="emit('close')">
    <div class="w-full max-w-md rounded-xl bg-card p-6 shadow-xl">
      <h3 class="mb-4 text-lg font-semibold">{{ task?.id ? '任务详情' : '添加今日任务' }}</h3>
      <form @submit.prevent="submit">
        <label class="mb-1 block text-sm text-sub">内容</label>
        <input v-model="form.title" type="text" required class="mb-3 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" />
        <div class="mb-3 grid grid-cols-2 gap-3">
          <div>
            <label class="mb-1 block text-sm text-sub">重要度</label>
            <select v-model="form.importance" class="w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none">
              <option :value="1">低</option>
              <option :value="2">中</option>
              <option :value="3">高</option>
            </select>
          </div>
          <div>
            <label class="mb-1 block text-sm text-sub">日期</label>
            <input v-model="form.date" type="date" required class="w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" />
          </div>
        </div>
        <label class="mb-1 block text-sm text-sub">所属计划（可留空）</label>
        <select v-model="form.planId" class="mb-3 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" @change="onPlanChange">
          <option :value="null">（不归属计划）</option>
          <option v-for="plan in plans" :key="plan.id" :value="plan.id">{{ plan.title }}</option>
        </select>
        <div v-if="!task?.id && form.planId && pickableSubs.length" class="mb-3 rounded-lg bg-teal-soft p-3">
          <p class="mb-2 text-xs font-semibold text-teal">从本周计划子任务挑选（点一个自动带过来）</p>
          <button
            v-for="sub in pickableSubs"
            :key="sub.id"
            type="button"
            class="mb-1 mr-1 rounded-full border px-3 py-1 text-xs"
            :class="form.subtaskId === sub.id ? 'border-teal bg-teal font-semibold text-white' : 'border-hairline bg-card text-sub hover:border-teal'"
            @click="pickSubtask(sub)"
          >
            {{ sub.name }}
          </button>
        </div>
        <label class="mb-1 block text-sm text-sub">备注</label>
        <textarea v-model="form.note" rows="3" class="mb-4 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none"></textarea>
        <div class="flex justify-between gap-2">
          <button v-if="task?.id" type="button" class="rounded-lg border border-red px-4 py-2 text-sm text-red hover:bg-red-soft" @click="emit('delete')">
            删除
          </button>
          <span v-else></span>
          <div class="flex gap-2">
            <button type="button" class="rounded-lg border border-hairline px-4 py-2 text-sm" @click="emit('close')">取消</button>
            <button type="submit" class="rounded-lg bg-teal px-4 py-2 text-sm font-semibold text-white hover:bg-teal-dark">保存</button>
          </div>
        </div>
      </form>
    </div>
  </BaseModal>
</template>
