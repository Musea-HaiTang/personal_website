<script setup>
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import api from '../api'
import { usePlansStore } from '../stores/plans'
import { isoWeek, today, weekEnd, weekStart } from '../utils/date'

// ---------- 日期工具 ----------
function formatWhen(iso) {
  if (!iso) return ''
  return iso.slice(5, 10).replace('-', '-') + ' ' + iso.slice(11, 16)
}

const weekLabel = computed(() => {
  const fmt = (s) => `${parseInt(s.slice(5, 7), 10)}月${parseInt(s.slice(8, 10), 10)}日`
  return `${weekStart.slice(0, 4)} 年第 ${isoWeek(weekStart)} 周 · ${fmt(weekStart)} – ${fmt(weekEnd)}`
})
const impLabels = { 1: '低', 2: '中', 3: '高' }
const impCls = { 1: 'bg-paper-soft text-sub', 2: 'bg-teal-soft text-teal', 3: 'bg-red-soft text-red' }
const planColors = ['#0e7c74', '#7c5cbf', '#3b6fd4', '#b7791f', '#c4533a']

// ---------- 状态 ----------
const activeTab = ref('today')
const plansStore = usePlansStore()
const { plans, todayTasks, allTasks, loaded } = storeToRefs(plansStore)
const error = ref('')
const selectedPlanId = ref(null)
const selectedPlan = computed(() => plans.value.find((p) => p.id === selectedPlanId.value) || null)

// 可记忆列宽
const colsTask = ref(localStorage.getItem('plan-cols-v2') || '24px 190px 1fr 2fr 56px')
const colsSub = ref(localStorage.getItem('plan-subcols-v2') || '24px 180px 2fr 70px 1fr 28px')

// ---------- 加载（会话级缓存，见 stores/plans.js） ----------
async function refresh() {
  await plansStore.refresh()
  if (selectedPlanId.value && !plans.value.some((p) => p.id === selectedPlanId.value)) {
    selectedPlanId.value = null
  }
  if (!selectedPlanId.value && plans.value.length) selectedPlanId.value = plans.value[0].id
}

// ---------- 计算 ----------
const weekStats = computed(() => {
  let total = 0
  let done = 0
  for (const p of plans.value) {
    total += p.subtasks.length
    done += p.subtasks.filter((s) => s.completed).length
  }
  for (const t of allTasks.value) {
    if (t.subtask_id) continue
    if (t.date >= weekStart && t.date <= weekEnd) {
      total += 1
      if (t.completed) done += 1
    }
  }
  const pct = total ? Math.round((done / total) * 100) : 0
  return { total, done, pct }
})
const unfinishedToday = computed(() => todayTasks.value.filter((t) => !t.completed))
const todayDoneCount = computed(() => todayTasks.value.filter((t) => t.completed).length)
const selectedDoneId = ref(null)
const doneTasks = computed(() =>
  allTasks.value
    .filter((t) => t.completed)
    .sort((a, b) => (b.completed_at || '').localeCompare(a.completed_at || ''))
)
const selectedDone = computed(() => doneTasks.value.find((t) => t.id === selectedDoneId.value) || null)
const doneGroups = computed(() => {
  const groups = {}
  for (const t of doneTasks.value) {
    const day = (t.completed_at || t.date || '').slice(0, 10)
    ;(groups[day] = groups[day] || []).push(t)
  }
  return Object.keys(groups).map((day) => ({ day, items: groups[day] }))
})
function planProgress(plan) {
  const total = plan.subtasks.length
  const done = plan.subtasks.filter((s) => s.completed).length
  return { total, done, pct: total ? Math.round((done / total) * 100) : 0 }
}

// ---------- 计划 CRUD ----------
const planModal = ref(false)
const planForm = ref({ id: null, title: '', importance: 2, note: '' })
function openPlanModal(plan = null) {
  planForm.value = plan
    ? { id: plan.id, title: plan.title, importance: plan.importance, note: plan.note || '' }
    : { id: null, title: '', importance: 2, note: '' }
  planModal.value = true
}
async function savePlan() {
  const payload = {
    title: planForm.value.title.trim(),
    importance: Number(planForm.value.importance),
    note: planForm.value.note.trim() || null,
    week_start: weekStart,
  }
  if (!payload.title) return
  try {
    if (planForm.value.id) await api.put(`/plans/${planForm.value.id}`, payload)
    else await api.post('/plans', payload)
    planModal.value = false
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存计划失败'
  }
}
async function deletePlan(plan) {
  if (!confirm(`确定删除计划「${plan.title}」？其子任务也会一并删除。`)) return
  try {
    await api.delete(`/plans/${plan.id}`)
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除计划失败'
  }
}

// ---------- 子任务 CRUD ----------
const subModal = ref(false)
const subForm = ref({ id: null, name: '', importance: 2, note: '' })
function openSubModal(subtask = null) {
  subForm.value = subtask
    ? { id: subtask.id, name: subtask.name, importance: subtask.importance, note: subtask.note || '' }
    : { id: null, name: '', importance: 2, note: '' }
  subModal.value = true
}
async function saveSubtask() {
  const payload = {
    name: subForm.value.name.trim(),
    importance: Number(subForm.value.importance),
    note: subForm.value.note.trim() || null,
  }
  if (!payload.name || !selectedPlan.value) return
  try {
    if (subForm.value.id) await api.put(`/subtasks/${subForm.value.id}`, payload)
    else await api.post(`/plans/${selectedPlan.value.id}/subtasks`, payload)
    subModal.value = false
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存子任务失败'
  }
}
async function toggleSubtask(subtask) {
  try {
    await api.put(`/subtasks/${subtask.id}`, { completed: !subtask.completed })
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '切换子任务失败'
  }
}
async function deleteSubtask(subtask) {
  if (!confirm(`确定删除子任务「${subtask.name}」？`)) return
  try {
    await api.delete(`/subtasks/${subtask.id}`)
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除子任务失败'
  }
}

// ---------- 今日任务 CRUD ----------
const taskModal = ref(false)
const taskForm = ref({ id: null, title: '', importance: 2, date: today, note: '', planId: null, subtaskId: null })
const pickedSub = ref(null)
const pickableSubs = computed(() => {
  const plan = plans.value.find((p) => p.id === Number(taskForm.value.planId))
  return plan ? plan.subtasks.filter((s) => !s.completed) : []
})
function openTaskModal(task = null) {
  pickedSub.value = null
  taskForm.value = task
    ? {
        id: task.id,
        title: task.title,
        importance: task.importance,
        date: task.date,
        note: task.note || '',
        planId: task.plan_id,
        subtaskId: task.subtask_id,
      }
    : { id: null, title: '', importance: 2, date: today, note: '', planId: null, subtaskId: null }
  taskModal.value = true
}
function onPlanChange() {
  taskForm.value.subtaskId = null
  pickedSub.value = null
}
function pickSubtask(sub) {
  pickedSub.value = sub
  taskForm.value.subtaskId = sub.id
  taskForm.value.title = sub.name
}
async function saveTask() {
  const payload = {
    title: taskForm.value.title.trim(),
    importance: Number(taskForm.value.importance),
    date: taskForm.value.date,
    note: taskForm.value.note.trim() || null,
    plan_id: taskForm.value.planId ? Number(taskForm.value.planId) : null,
    subtask_id: taskForm.value.subtaskId ? Number(taskForm.value.subtaskId) : null,
  }
  if (!payload.title || !payload.date) return
  try {
    if (taskForm.value.id) await api.put(`/tasks/${taskForm.value.id}`, payload)
    else await api.post('/tasks', payload)
    taskModal.value = false
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存任务失败'
  }
}
async function toggleTask(task) {
  try {
    await api.put(`/tasks/${task.id}`, { completed: !task.completed })
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '切换任务失败'
  }
}
async function deleteTask(task) {
  if (!confirm(`确定删除任务「${task.title}」？`)) return
  try {
    await api.delete(`/tasks/${task.id}`)
    taskModal.value = false
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除任务失败'
  }
}

// ---------- 复盘 / 顺延 ----------
const reviewModal = ref(false)
const reviewTask = ref(null)
const reviewNote = ref('')
function openReview(task) {
  reviewTask.value = task
  reviewNote.value = task.review_note || ''
  reviewModal.value = true
}
async function rolloverOne(task, note = '') {
  try {
    if (note) await api.put(`/tasks/${task.id}`, { review_note: note })
    await api.post(`/tasks/${task.id}/rollover`)
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '顺延失败'
  }
}
async function confirmRollover() {
  if (!reviewTask.value) return
  await rolloverOne(reviewTask.value, reviewNote.value.trim())
  reviewModal.value = false
}
async function rolloverAll() {
  for (const task of unfinishedToday.value) {
    await rolloverOne(task)
  }
}
async function reopenTask(task) {
  if (!confirm(`确定把「${task.title}」重新打开，回到今日列表吗？`)) return
  try {
    await api.put(`/tasks/${task.id}`, { completed: false })
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '重新打开失败'
  }
}

// ---------- 导出 ----------
async function exportWeek() {
  try {
    const { data } = await api.get('/plans/week/export', {
      params: { week_start: weekStart },
      responseType: 'blob',
    })
    const url = URL.createObjectURL(data)
    const a = document.createElement('a')
    a.href = url
    a.download = `周计划-${weekStart}.md`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    error.value = e.response?.data?.detail || '导出失败'
  }
}

// ---------- 列宽拖拽（记录抓取偏移，只移动被拖的边界） ----------
function startResize(e, table, col) {
  e.preventDefault()
  const header = table === 'task' ? document.getElementById('task-head') : document.getElementById('sub-head')
  const cs = getComputedStyle(header)
  const widths = cs.gridTemplateColumns.split(' ').map((x) => parseFloat(x))
  const gap = parseFloat(cs.columnGap || cs.gap) || 0
  const left = header.getBoundingClientRect().left + parseFloat(cs.paddingLeft || '0')
  let boundary = gap * (col - 1)
  for (let i = 1; i <= col; i++) boundary += widths[i - 1]
  const bPrev = boundary - gap - widths[col - 1]
  const bNext = boundary + gap + widths[col]
  const offset = boundary - (e.clientX - left)
  const moving = (ev) => {
    let b = ev.clientX - left + offset
    const minB = bPrev + gap + 48
    const maxB = bNext - gap - 48
    if (b < minB) b = minB
    if (b > maxB) b = maxB
    const arr = widths.slice()
    arr[col - 1] = b - bPrev - gap
    arr[col] = bNext - b - gap
    arr[4] = 'minmax(0,1fr)'
    const tpl = arr.map((v, i) => (i === 4 ? v : v + 'px')).join(' ')
    if (table === 'task') colsTask.value = tpl
    else colsSub.value = tpl
  }
  const up = () => {
    document.removeEventListener('mousemove', moving)
    document.removeEventListener('mouseup', up)
    document.body.classList.remove('select-none')
    const tpl = table === 'task' ? colsTask.value : colsSub.value
    localStorage.setItem(table === 'task' ? 'plan-cols-v2' : 'plan-subcols-v2', tpl)
  }
  document.body.classList.add('select-none')
  document.addEventListener('mousemove', moving)
  document.addEventListener('mouseup', up)
}

onMounted(async () => {
  if (!plansStore.loaded) await refresh()
})
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <p class="text-xs font-semibold tracking-widest text-teal">{{ weekLabel }}</p>
      <div class="flex items-center gap-3">
        <span class="inline-flex items-center gap-2 rounded-full border border-hairline bg-card px-3 py-1.5 text-xs text-sub">
          本周完成度 <b class="text-ink">{{ weekStats.pct }}%</b>
          <span class="h-1.5 w-16 overflow-hidden rounded-full bg-hairline">
            <span class="block h-full rounded-full bg-teal" :style="{ width: weekStats.pct + '%' }"></span>
          </span>
        </span>
        <button
          class="rounded-lg border border-hairline bg-card px-3 py-1.5 text-xs font-semibold text-sub hover:border-teal hover:text-teal"
          @click="exportWeek"
        >
          导出本周
        </button>
      </div>
    </div>

    <p v-if="error || plansStore.error" class="mb-4 rounded bg-red-soft px-3 py-2 text-sm text-red">{{ error || plansStore.error }}</p>
    <div class="mb-5 flex gap-2 border-b border-hairline pb-3">
      <button
        v-for="tab in [
          { key: 'today', label: '今日' },
          { key: 'plan', label: '本周计划' },
          { key: 'done', label: '已完成' },
          { key: 'review', label: '复盘' },
        ]"
        :key="tab.key"
        class="rounded-lg px-4 py-2 text-sm font-medium text-sub hover:bg-paper-soft"
        :class="{ 'bg-card text-teal shadow-sm ring-1 ring-hairline': activeTab === tab.key }"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 今日 -->
    <div v-if="activeTab === 'today'">
      <div class="overflow-hidden rounded-lg border border-hairline bg-card shadow-sm">
        <div class="flex items-center justify-between border-b border-hairline px-4 py-3">
          <h3 class="text-sm font-semibold text-ink">今日执行 · {{ today }}</h3>
          <button class="rounded bg-teal px-3 py-1.5 text-xs font-semibold text-white hover:bg-teal-dark" @click="openTaskModal()">
            ＋ 添加任务
          </button>
        </div>
<div id="task-head" class="grid gap-x-2 bg-paper-soft px-4 py-2 text-xs font-semibold text-sub" :style="{ gridTemplateColumns: colsTask }">
          <span></span>
          <span class="relative">名字<span class="resize-handle" @mousedown="startResize($event, 'task', 2)"></span></span>
          <span class="relative">标签<span class="resize-handle" @mousedown="startResize($event, 'task', 3)"></span></span>
          <span class="relative">备注<span class="resize-handle" @mousedown="startResize($event, 'task', 4)"></span></span>
          <span>重要度</span>
        </div>
        <div v-if="loaded && !unfinishedToday.length" class="px-4 py-8 text-center text-sm text-sub">今天没有待办，点「添加任务」安排一件吧。</div>
        <div
          v-for="task in unfinishedToday"
          :key="task.id"
          class="grid cursor-pointer items-center gap-x-2 border-b border-hairline px-4 py-2.5 text-sm hover:bg-paper-soft"
          :style="{ gridTemplateColumns: colsTask }"
          @click="openTaskModal(task)"
        >
          <span class="check-circle" :class="{ on: task.completed }" @click.stop="toggleTask(task)"></span>
          <span class="truncate font-medium text-ink">{{ task.title }}</span>
          <span>
            <span v-if="task.plan_title" class="inline-flex items-center gap-1 rounded-full bg-paper-soft px-2 py-0.5 text-[11px] text-sub">
              <i class="h-1.5 w-1.5 rounded-full" :style="{ background: planColors[task.plan_id % planColors.length] }"></i>
              {{ task.plan_title }}
            </span>
          </span>
          <span class="truncate text-xs text-sub">{{ task.note }}</span>
          <span class="w-fit rounded px-2 py-0.5 text-[11px] font-bold" :class="impCls[task.importance]">{{ impLabels[task.importance] }}</span>
        </div>
        <div class="flex items-center gap-3 border-t border-hairline bg-paper-soft px-4 py-2.5 text-xs text-sub">
          今日进度
          <b class="text-ink">{{ todayDoneCount }}/{{ todayTasks.length }}</b>
        </div>
      </div>
    </div>

    <!-- 本周计划 -->
    <div v-if="activeTab === 'plan'">
      <div class="mb-4 flex items-center justify-between">
        <div>
          <h3 class="text-base font-semibold">本周计划</h3>
          <p class="text-xs text-sub">点计划卡片，右侧管理子任务 · 中途可随时加新计划</p>
        </div>
        <button class="rounded bg-teal px-3 py-1.5 text-xs font-semibold text-white hover:bg-teal-dark" @click="openPlanModal()">＋ 添加计划</button>
      </div>
      <div class="grid items-start gap-4" style="grid-template-columns: 300px 1fr">
        <div class="flex flex-col gap-2">
          <button
            v-for="plan in plans"
            :key="plan.id"
            class="relative rounded-2xl border border-hairline bg-card p-5 pl-6 text-left transition hover:border-teal"
            :class="{ 'ring-1 ring-teal': selectedPlanId === plan.id }"
            @click="selectedPlanId = plan.id"
          >
            <span class="absolute left-0 top-5 bottom-5 w-[3px] rounded-r" :style="{ background: planColors[plan.id % planColors.length] }"></span>
            <span
              v-if="planProgress(plan).total && planProgress(plan).done === planProgress(plan).total"
              class="absolute right-3 top-3 rounded-full bg-green px-2 py-0.5 text-[10px] font-bold text-white"
            >
              已完成
            </span>
            <div class="flex items-center gap-3">
              <svg class="h-14 w-14 shrink-0" viewBox="0 0 58 58">
                <circle cx="29" cy="29" r="20" fill="none" stroke="#ece5da" stroke-width="5" />
                <circle
                  cx="29"
                  cy="29"
                  r="20"
                  fill="none"
                  :stroke="planColors[plan.id % planColors.length]"
                  stroke-width="5"
                  stroke-linecap="round"
                  :stroke-dasharray="125.6"
                  :stroke-dashoffset="125.6 * (1 - planProgress(plan).pct / 100)"
                  transform="rotate(-90 29 29)"
                />
                <text x="29" y="33" text-anchor="middle" class="text-[10px] font-bold" fill="#2b2622">
                  {{ planProgress(plan).pct }}%
                </text>
              </svg>
              <div class="min-w-0">
                <p class="truncate font-serif font-semibold text-ink">{{ plan.title }}</p>
                <p class="mt-1 flex items-center gap-2 text-xs text-sub">
                  {{ planProgress(plan).done }}/{{ planProgress(plan).total }} 子任务
                  <span class="rounded px-1.5 py-0.5 text-[10px] font-bold" :class="impCls[plan.importance]">{{ impLabels[plan.importance] }}</span>
                </p>
              </div>
            </div>
          </button>
          <p v-if="loaded && !plans.length" class="rounded-xl border border-dashed border-hairline p-6 text-center text-sm text-sub">本周还没有计划，先加一个吧。</p>
        </div>

        <div v-if="selectedPlan" class="rounded-2xl border border-hairline bg-card p-5">
          <div class="mb-4 flex items-center justify-between gap-3">
            <div class="flex items-center gap-3">
              <svg class="h-12 w-12 shrink-0" viewBox="0 0 58 58">
                <circle cx="29" cy="29" r="20" fill="none" stroke="#ece5da" stroke-width="5" />
                <circle
                  cx="29"
                  cy="29"
                  r="20"
                  fill="none"
                  :stroke="planColors[selectedPlan.id % planColors.length]"
                  stroke-width="5"
                  stroke-linecap="round"
                  :stroke-dasharray="125.6"
                  :stroke-dashoffset="125.6 * (1 - planProgress(selectedPlan).pct / 100)"
                  transform="rotate(-90 29 29)"
                />
                <text x="29" y="33" text-anchor="middle" class="text-[10px] font-bold" fill="#2b2622">{{ planProgress(selectedPlan).pct }}%</text>
              </svg>
              <div>
                <p class="flex items-center gap-2 font-serif text-lg font-semibold text-ink">
                  {{ selectedPlan.title }}
                  <span class="rounded px-1.5 py-0.5 text-[10px] font-bold" :class="impCls[selectedPlan.importance]">{{ impLabels[selectedPlan.importance] }}</span>
                </p>
                <p class="text-xs text-sub">{{ planProgress(selectedPlan).done }}/{{ planProgress(selectedPlan).total }} 子任务</p>
              </div>
            </div>
            <div class="flex items-center gap-2">
              <button class="rounded-lg border border-hairline px-3 py-1.5 text-xs font-semibold text-sub hover:border-teal hover:text-teal" @click="openPlanModal(selectedPlan)">
                编辑计划
              </button>
              <button class="rounded-lg border border-hairline px-3 py-1.5 text-xs font-semibold text-sub hover:border-red hover:text-red" @click="deletePlan(selectedPlan)">
                删除计划
              </button>
              <button
                class="rounded px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90"
                :style="{ background: planColors[selectedPlan.id % planColors.length] }"
                @click="openSubModal()"
              >
                ＋ 添加子任务
              </button>
            </div>
          </div>
          <div id="sub-head" class="grid gap-x-2 bg-paper-soft px-4 py-2 text-xs font-semibold text-sub" :style="{ gridTemplateColumns: colsSub }">
            <span></span>
            <span class="relative">名字<span class="resize-handle" @mousedown="startResize($event, 'sub', 2)"></span></span>
            <span class="relative">备注<span class="resize-handle" @mousedown="startResize($event, 'sub', 3)"></span></span>
            <span class="relative">重要度<span class="resize-handle" @mousedown="startResize($event, 'sub', 4)"></span></span>
            <span>状态</span>
            <span></span>
          </div>
          <div v-if="loaded && !selectedPlan.subtasks.length" class="px-4 py-6 text-center text-sm text-sub">还没有子任务，点右上角「添加子任务」加一条吧。</div>
          <div
            v-for="sub in selectedPlan.subtasks"
            :key="sub.id"
            class="grid cursor-pointer items-center gap-x-2 border-b border-hairline px-4 py-2 text-sm last:border-b-0 hover:bg-paper-soft"
            :style="{ gridTemplateColumns: colsSub }"
            @click="openSubModal(sub)"
          >
            <span class="check-circle" :class="{ on: sub.completed }" @click.stop="toggleSubtask(sub)"></span>
            <span class="truncate font-medium" :class="sub.completed ? 'text-sub line-through' : 'text-ink'">{{ sub.name }}</span>
            <span class="truncate text-xs text-sub">{{ sub.note }}</span>
            <span class="w-fit rounded px-2 py-0.5 text-[11px] font-bold" :class="impCls[sub.importance]">{{ impLabels[sub.importance] }}</span>
            <span class="text-xs" :class="sub.completed ? 'text-green' : 'text-sub'">
              {{ sub.completed ? '完成于 ' + formatWhen(sub.completed_at) : '待完成' }}
            </span>
            <button class="justify-self-start text-hairline hover:text-red" title="删除子任务" @click.stop="deleteSubtask(sub)">×</button>
          </div>
        </div>
        <div v-else-if="loaded" class="rounded-xl border border-dashed border-hairline p-10 text-center text-sm text-sub">从左侧选择一个计划，查看和管理子任务</div>
      </div>
    </div>

    <!-- 已完成 -->
    <div v-if="activeTab === 'done'">
      <div class="grid items-start gap-0 overflow-hidden rounded-lg border border-hairline bg-card shadow-sm" style="grid-template-columns: 320px 1fr">
        <div class="max-h-[60vh] overflow-auto border-r border-hairline p-2">
          <template v-for="group in doneGroups" :key="group.day">
            <p class="px-3 pb-1 pt-3 text-xs font-bold tracking-wide text-sub">{{ group.day }}</p>
            <button
              v-for="task in group.items"
              :key="task.id"
              class="flex w-full flex-col gap-0.5 rounded-lg px-3 py-2 text-left hover:bg-paper-soft"
              @click="selectedDoneId = task.id"
            >
              <span class="text-sm font-medium text-ink">{{ task.title }}</span>
              <span class="text-[11px] text-sub">{{ task.plan_title || '无计划' }} · {{ impLabels[task.importance] }} · {{ formatWhen(task.completed_at) }}</span>
            </button>
          </template>
          <p v-if="loaded && !doneGroups.length" class="p-6 text-center text-sm text-sub">还没有完成过的任务</p>
        </div>
        <div class="p-5">
          <template v-if="selectedDone">
            <h4 class="text-lg font-semibold text-ink">{{ selectedDone.title }}</h4>
            <div class="mt-2 flex flex-wrap gap-2">
              <span class="rounded px-2 py-0.5 text-[11px] font-bold" :class="impCls[selectedDone.importance]">{{ impLabels[selectedDone.importance] }}</span>
              <span v-if="selectedDone.plan_title" class="rounded-full bg-paper-soft px-2 py-0.5 text-[11px] text-sub">{{ selectedDone.plan_title }}</span>
            </div>
            <p class="mt-3 text-sm leading-relaxed text-sub">{{ selectedDone.note || '没有备注' }}</p>
            <p class="mt-3 text-xs text-sub">完成于 {{ formatWhen(selectedDone.completed_at) }}</p>
            <button class="mt-4 rounded-lg border border-hairline px-3 py-1.5 text-xs font-semibold text-sub hover:border-teal hover:text-teal" @click="reopenTask(selectedDone)">
              重新打开
            </button>
          </template>
          <p v-else class="text-sm text-sub">选中左侧任务查看详情</p>
        </div>
      </div>
    </div>

    <!-- 复盘 -->
    <div v-if="activeTab === 'review'">
      <div class="grid items-start gap-0 overflow-hidden rounded-lg border border-hairline bg-card shadow-sm" style="grid-template-columns: 1.2fr 0.8fr">
        <div class="border-r border-hairline p-5">
          <h4 class="mb-2 text-sm font-semibold text-ink">未完成 · {{ unfinishedToday.length }} 项</h4>
          <div v-for="task in unfinishedToday" :key="task.id" class="flex items-center gap-3 border-t border-dashed border-hairline py-3 text-sm">
            <span class="check-circle" :class="{ on: task.completed }" @click="toggleTask(task)"></span>
            <span class="flex-1 cursor-pointer font-medium text-teal" @click="openReview(task)">{{ task.title }}</span>
            <span v-if="task.plan_title" class="rounded-full bg-paper-soft px-2 py-0.5 text-[11px] text-sub">{{ task.plan_title }}</span>
          </div>
          <p v-if="loaded && !unfinishedToday.length" class="py-6 text-center text-sm text-sub">今天都完成了，真棒。</p>
          <button class="mt-4 w-full rounded-lg bg-teal py-2 text-sm font-semibold text-white hover:bg-teal-dark" @click="rolloverAll">全部顺延到明天</button>
        </div>
        <div class="bg-paper-soft p-5">
          <h4 class="mb-2 text-sm font-semibold text-ink">今日回顾</h4>
          <div class="flex items-center justify-between border-t border-dashed border-hairline py-2.5 text-sm">
            <span class="text-sub">今日完成</span><b class="text-ink">{{ doneTasks.length }} 项</b>
          </div>
          <div class="flex items-center justify-between border-t border-dashed border-hairline py-2.5 text-sm">
            <span class="text-sub">本周完成度</span><b class="text-ink">{{ weekStats.pct }}%</b>
          </div>
          <div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-hairline">
            <span class="block h-full rounded-full bg-green" :style="{ width: weekStats.pct + '%' }"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 任务弹窗（新增 / 详情编辑） -->
    <div v-if="taskModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" @click.self="taskModal = false">
      <div class="w-full max-w-md rounded-xl bg-card p-6 shadow-xl">
        <h3 class="mb-4 text-lg font-semibold">{{ taskForm.id ? '任务详情' : '添加今日任务' }}</h3>
        <form @submit.prevent="saveTask">
          <label class="mb-1 block text-sm text-sub">内容</label>
          <input v-model="taskForm.title" type="text" required class="mb-3 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" />
          <div class="mb-3 grid grid-cols-2 gap-3">
            <div>
              <label class="mb-1 block text-sm text-sub">重要度</label>
              <select v-model="taskForm.importance" class="w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none">
                <option :value="1">低</option>
                <option :value="2">中</option>
                <option :value="3">高</option>
              </select>
            </div>
            <div>
              <label class="mb-1 block text-sm text-sub">日期</label>
              <input v-model="taskForm.date" type="date" required class="w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" />
            </div>
          </div>
          <label class="mb-1 block text-sm text-sub">所属计划（可留空）</label>
          <select v-model="taskForm.planId" class="mb-3 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" @change="onPlanChange">
            <option :value="null">（不归属计划）</option>
            <option v-for="plan in plans" :key="plan.id" :value="plan.id">{{ plan.title }}</option>
          </select>
          <div v-if="!taskForm.id && taskForm.planId && pickableSubs.length" class="mb-3 rounded-lg bg-teal-soft p-3">
            <p class="mb-2 text-xs font-semibold text-teal">从本周计划子任务挑选（点一个自动带过来）</p>
            <button
              v-for="sub in pickableSubs"
              :key="sub.id"
              type="button"
              class="mb-1 mr-1 rounded-full border px-3 py-1 text-xs"
              :class="taskForm.subtaskId === sub.id ? 'border-teal bg-teal font-semibold text-white' : 'border-hairline bg-card text-sub hover:border-teal'"
              @click="pickSubtask(sub)"
            >
              {{ sub.name }}
            </button>
          </div>
          <label class="mb-1 block text-sm text-sub">备注</label>
          <textarea v-model="taskForm.note" rows="3" class="mb-4 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none"></textarea>
          <div class="flex justify-between gap-2">
            <button v-if="taskForm.id" type="button" class="rounded-lg border border-red px-4 py-2 text-sm text-red hover:bg-red-soft" @click="deleteTask(taskForm)">
              删除
            </button>
            <span v-else></span>
            <div class="flex gap-2">
              <button type="button" class="rounded-lg border border-hairline px-4 py-2 text-sm" @click="taskModal = false">取消</button>
              <button type="submit" class="rounded-lg bg-teal px-4 py-2 text-sm font-semibold text-white hover:bg-teal-dark">保存</button>
            </div>
          </div>
        </form>
      </div>
    </div>

    <!-- 计划弹窗 -->
    <div v-if="planModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" @click.self="planModal = false">
      <div class="w-full max-w-md rounded-xl bg-card p-6 shadow-xl">
        <h3 class="mb-4 text-lg font-semibold">{{ planForm.id ? '编辑计划' : '添加本周计划' }}</h3>
        <form @submit.prevent="savePlan">
          <label class="mb-1 block text-sm text-sub">计划名称</label>
          <input v-model="planForm.title" type="text" required class="mb-3 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" />
          <label class="mb-1 block text-sm text-sub">重要度</label>
          <select v-model="planForm.importance" class="mb-3 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none">
            <option :value="1">低</option>
            <option :value="2">中</option>
            <option :value="3">高</option>
          </select>
          <label class="mb-1 block text-sm text-sub">备注（可选）</label>
          <textarea v-model="planForm.note" rows="2" class="mb-4 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none"></textarea>
          <div class="flex justify-end gap-2">
            <button type="button" class="rounded-lg border border-hairline px-4 py-2 text-sm" @click="planModal = false">取消</button>
            <button type="submit" class="rounded-lg bg-teal px-4 py-2 text-sm font-semibold text-white hover:bg-teal-dark">保存</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 子任务弹窗 -->
    <div v-if="subModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" @click.self="subModal = false">
      <div class="w-full max-w-md rounded-xl bg-card p-6 shadow-xl">
        <h3 class="mb-4 text-lg font-semibold">{{ subForm.id ? '编辑子任务' : '添加子任务' }}</h3>
        <form @submit.prevent="saveSubtask">
          <label class="mb-1 block text-sm text-sub">名字</label>
          <input v-model="subForm.name" type="text" required class="mb-3 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" />
          <label class="mb-1 block text-sm text-sub">重要度</label>
          <select v-model="subForm.importance" class="mb-3 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none">
            <option :value="1">低</option>
            <option :value="2">中</option>
            <option :value="3">高</option>
          </select>
          <label class="mb-1 block text-sm text-sub">备注（可选）</label>
          <textarea v-model="subForm.note" rows="2" class="mb-4 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none"></textarea>
          <div class="flex justify-end gap-2">
            <button type="button" class="rounded-lg border border-hairline px-4 py-2 text-sm" @click="subModal = false">取消</button>
            <button type="submit" class="rounded-lg bg-teal px-4 py-2 text-sm font-semibold text-white hover:bg-teal-dark">保存</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 复盘弹窗 -->
    <div v-if="reviewModal && reviewTask" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4" @click.self="reviewModal = false">
      <div class="w-full max-w-md rounded-xl bg-card p-6 shadow-xl">
        <h3 class="mb-4 text-lg font-semibold">计划复盘</h3>
        <p class="mb-1 text-sm text-sub">任务</p>
        <p class="mb-4 rounded-lg border border-hairline bg-paper-soft px-3 py-2 text-sm font-semibold text-ink">{{ reviewTask.title }}</p>
        <label class="mb-1 block text-sm text-sub">说明（可选）</label>
        <textarea v-model="reviewNote" rows="3" class="mb-4 w-full rounded-lg border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="写下为什么没完成，方便之后复盘…"></textarea>
        <div class="flex justify-end gap-2">
          <button class="rounded-lg border border-hairline px-4 py-2 text-sm" @click="reviewModal = false">取消</button>
          <button class="rounded-lg bg-teal px-4 py-2 text-sm font-semibold text-white hover:bg-teal-dark" @click="confirmRollover">顺延到明天</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.resize-handle {
  position: absolute;
  right: -7px;
  top: -8px;
  bottom: -8px;
  width: 14px;
  cursor: col-resize;
  z-index: 3;
}
.resize-handle::after {
  content: '';
  position: absolute;
  top: 4px;
  bottom: 4px;
  right: 6px;
  width: 1px;
  background: #e9e3d9;
}
.resize-handle:hover::after {
  background: #0e7c74;
}
.check-circle {
  width: 20px;
  height: 20px;
  border: 2px solid #d5cdbf;
  border-radius: 50%;
  flex: none;
  cursor: pointer;
  display: inline-grid;
  place-items: center;
  transition: 0.15s;
  background: transparent;
}
.check-circle.on {
  background: #3d9970;
  border-color: #3d9970;
}
.check-circle.on::after {
  content: '✓';
  color: #fff;
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
}
</style>
