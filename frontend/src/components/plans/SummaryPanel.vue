<script setup>
import { ref, watch } from 'vue'

import { usePlansStore } from '../../stores/plans'
import { addDays, isoWeek } from '../../utils/date'

const props = defineProps({
  weekStart: { type: String, required: true },
})

const store = usePlansStore()
const summary = ref(null)
const reflection = ref('')
const nextPlan = ref('')
const error = ref('')
const saving = ref(false)

const fmt = (s) => `${parseInt(s.slice(5, 7), 10)}月${parseInt(s.slice(8, 10), 10)}日`
const weekLabel = () => {
  const ws = props.weekStart
  return `${ws.slice(0, 4)} 年第 ${isoWeek(ws)} 周 · ${fmt(ws)} – ${fmt(addDays(ws, 6))}`
}
const savedAt = () => (summary.value?.updated_at ? summary.value.updated_at.replace('T', ' ').slice(0, 16) : '')

async function load() {
  error.value = ''
  try {
    const data = await store.fetchSummary(props.weekStart)
    summary.value = data
    reflection.value = data.reflection || ''
    nextPlan.value = data.next_plan || ''
  } catch (e) {
    error.value = e.response?.data?.detail || '周总结加载失败'
  }
}

async function save() {
  saving.value = true
  try {
    await store.saveSummary(props.weekStart, { reflection: reflection.value, next_plan: nextPlan.value })
    await load()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

watch(() => props.weekStart, load, { immediate: true })
</script>

<template>
  <div class="card">
    <div class="section">
      <h3 class="serif">周总结 · {{ weekLabel() }}</h3>
      <span class="summeta">任何一周都能回顾并修改</span>
    </div>

    <p v-if="error" class="mb-4 rounded bg-red-soft px-3 py-2 text-sm text-red">{{ error }}</p>

    <div class="sum-edit">
      <div class="sumfield">
        <label>本周完成 <span class="summeta">（自动 · 来自该周已完成任务，只读）</span></label>
        <ul v-if="summary?.done?.length" class="sum-list done-list">
          <li v-for="item in summary.done" :key="item.kind + item.title">{{ item.title }}</li>
        </ul>
        <p v-else class="summeta">（该周暂无完成记录）</p>
      </div>

      <div class="sumfield">
        <label>未完成 / 卡点 <span class="summeta">（自动 · 来自该周未完成任务，只读）</span></label>
        <ul v-if="summary?.undone?.length" class="sum-list undone-list">
          <li v-for="item in summary.undone" :key="item.kind + item.title">{{ item.title }}</li>
        </ul>
        <p v-else class="summeta">（该周全部完成）</p>
      </div>

      <div class="sumfield">
        <label>收获与反思 <span class="summeta">（手动，可编辑）</span></label>
        <textarea v-model="reflection" placeholder="写下这周的收获与反思…"></textarea>
      </div>

      <div class="sumfield">
        <label>下周重点 <span class="summeta">（手动，可编辑）</span></label>
        <textarea v-model="nextPlan" placeholder="写下下周的重点…"></textarea>
      </div>
    </div>

    <div class="sumbar">
      <span class="summeta">{{ savedAt() ? '上次保存：' + savedAt() : '尚未保存过' }}</span>
      <button class="btn-teal" :disabled="saving" @click="save">{{ saving ? '保存中…' : '保存总结' }}</button>
    </div>
  </div>
</template>

<style scoped>
.card {
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 14px;
  padding: 18px 20px;
}
.section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--hairline);
  padding-bottom: 12px;
  margin-bottom: 14px;
}
.section h3 {
  font-size: 15px;
  font-weight: 600;
  color: var(--ink);
}
.serif {
  font-family: var(--serif);
}
.summeta {
  font-size: 11px;
  color: var(--sub);
}
.sum-edit {
  display: grid;
  gap: 14px;
}
.sumfield label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--sub);
  margin-bottom: 6px;
}
.sumfield textarea {
  width: 100%;
  border: 1px solid var(--hairline);
  border-radius: 9px;
  background: var(--paper-soft);
  padding: 10px 12px;
  font-size: 13px;
  color: var(--ink);
  font-family: var(--sans);
  resize: vertical;
  min-height: 68px;
}
.sumfield textarea:focus {
  outline: none;
  border-color: var(--teal);
  background: #fff;
}
.sum-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 6px;
}
.sum-list li {
  font-size: 13px;
  color: var(--ink);
  padding: 8px 12px;
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 9px;
}
.sum-list.done-list li::before {
  content: '✓ ';
  color: var(--green);
  font-weight: 700;
}
.sum-list.undone-list li::before {
  content: '○ ';
  color: var(--sub);
  font-weight: 700;
}
.sumbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 10px;
}
.btn-teal {
  background: var(--teal);
  border-color: var(--teal);
  color: #fff;
  border-radius: 8px;
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
.btn-teal:hover {
  background: var(--teal-dark);
  border-color: var(--teal-dark);
  color: #fff;
}
.btn-teal:disabled {
  opacity: 0.6;
  cursor: default;
}
</style>
