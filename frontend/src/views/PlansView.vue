<script setup>
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'

import PlanModal from '../components/plans/PlanModal.vue'
import ReviewModal from '../components/plans/ReviewModal.vue'
import StatsPanel from '../components/plans/StatsPanel.vue'
import SummaryPanel from '../components/plans/SummaryPanel.vue'
import SubtaskModal from '../components/plans/SubtaskModal.vue'
import TaskModal from '../components/plans/TaskModal.vue'
import { usePlansStore } from '../stores/plans'
import { addDays, isoWeek, today, weekStart } from '../utils/date'

// ---------- 日期与展示 ----------
function formatWhen(iso) {
  if (!iso) return ''
  return iso.slice(5, 10).replace('-', '-') + ' ' + iso.slice(11, 16)
}
const fmt = (s) => `${parseInt(s.slice(5, 7), 10)}月${parseInt(s.slice(8, 10), 10)}日`

// 所选周（默认本周，会话级）
const selectedWeek = ref(weekStart)
const selectedWeekEnd = computed(() => addDays(selectedWeek.value, 6))
const isCurrentWeek = computed(() => selectedWeek.value === weekStart)
const isPast = computed(() => !isCurrentWeek.value)

const weekLabel = computed(() => {
  return `${selectedWeek.value.slice(0, 4)} 年第 ${isoWeek(selectedWeek.value)} 周 · ${fmt(selectedWeek.value)} – ${fmt(selectedWeekEnd.value)}`
})
const todayLabel = computed(() =>
  isCurrentWeek.value
    ? `今日执行 · ${today}`
    : `本周任务 · ${fmt(selectedWeek.value)} – ${fmt(selectedWeekEnd.value)}`
)
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
const statData = ref(null)
const statError = ref('')

async function loadStats() {
  try {
    statData.value = await plansStore.fetchStats(12)
  } catch (e) {
    statError.value = e.response?.data?.detail || '统计加载失败'
  }
}
function selectTab(key) {
  activeTab.value = key
  if (key === 'stat' && !statData.value) loadStats()
}

// 可记忆列宽
const colsTask = ref(localStorage.getItem('plan-cols-v2') || '24px 190px 1fr 2fr 56px')
const colsSub = ref(localStorage.getItem('plan-subcols-v2') || '24px 180px 2fr 70px 1fr 28px')

// ---------- 周导航 ----------
function moveWeek(delta) {
  const next = addDays(selectedWeek.value, delta * 7)
  selectedWeek.value = next > weekStart ? weekStart : next
  refresh()
}
function goThisWeek() {
  selectedWeek.value = weekStart
  refresh()
}

// ---------- 加载（会话级缓存，见 stores/plans.js） ----------
async function refresh() {
  await plansStore.refresh(selectedWeek.value)
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
    if (t.date >= selectedWeek.value && t.date <= selectedWeekEnd.value) {
      total += 1
      if (t.completed) done += 1
    }
  }
  const pct = total ? Math.round((done / total) * 100) : 0
  return { total, done, pct }
})
// 视图作用域：本周 = 今日任务；过往周 = 该周全部任务（只读）
const viewTasks = computed(() =>
  isCurrentWeek.value
    ? todayTasks.value
    : allTasks.value.filter((t) => t.date >= selectedWeek.value && t.date <= selectedWeekEnd.value)
)
const viewUnfinished = computed(() => viewTasks.value.filter((t) => !t.completed))
const viewDoneCount = computed(() => viewTasks.value.filter((t) => t.completed).length)
const selectedDoneId = ref(null)
const doneTasks = computed(() =>
  allTasks.value
    .filter(
      (t) =>
        t.completed &&
        ((t.completed_at || t.date || '').slice(0, 10) >= selectedWeek.value) &&
        ((t.completed_at || t.date || '').slice(0, 10) <= selectedWeekEnd.value)
    )
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
const planEditing = ref(null)
function openPlanModal(plan = null) {
  if (isPast.value) return
  planEditing.value = plan
  planModal.value = true
}
async function savePlan(payload) {
  if (!payload.title) return
  try {
    await plansStore.savePlan({ ...payload, id: planEditing.value?.id ?? null, week_start: selectedWeek.value })
    planModal.value = false
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存计划失败'
  }
}
async function deletePlan(plan) {
  if (isPast.value) return
  if (!confirm(`确定删除计划「${plan.title}」？其子任务也会一并删除。`)) return
  try {
    await plansStore.deletePlan(plan.id)
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除计划失败'
  }
}

// ---------- 子任务 CRUD ----------
const subModal = ref(false)
const subEditing = ref(null)
function openSubModal(subtask = null) {
  if (isPast.value) return
  subEditing.value = subtask
  subModal.value = true
}
async function saveSubtask(payload) {
  if (!payload.name || !selectedPlan.value) return
  try {
    await plansStore.saveSubtask({ ...payload, id: subEditing.value?.id ?? null, plan_id: selectedPlan.value.id })
    subModal.value = false
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存子任务失败'
  }
}
async function toggleSubtask(subtask) {
  if (isPast.value) return
  try {
    await plansStore.updateSubtask(subtask.id, { completed: !subtask.completed })
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '切换子任务失败'
  }
}
async function deleteSubtask(subtask) {
  if (isPast.value) return
  if (!confirm(`确定删除子任务「${subtask.name}」？`)) return
  try {
    await plansStore.deleteSubtask(subtask.id)
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除子任务失败'
  }
}

// ---------- 今日任务 CRUD ----------
const taskModal = ref(false)
const taskEditing = ref(null)
function openTaskModal(task = null) {
  if (isPast.value) return
  taskEditing.value = task
  taskModal.value = true
}
async function saveTask(payload) {
  try {
    await plansStore.saveTask({ ...payload, id: taskEditing.value?.id ?? null })
    taskModal.value = false
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存任务失败'
  }
}
async function toggleTask(task) {
  if (isPast.value) return
  try {
    await plansStore.updateTask(task.id, { completed: !task.completed })
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '切换任务失败'
  }
}
async function deleteTask() {
  if (isPast.value) return
  if (!taskEditing.value) return
  if (!confirm(`确定删除任务「${taskEditing.value.title}」？`)) return
  try {
    await plansStore.deleteTask(taskEditing.value.id)
    taskModal.value = false
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除任务失败'
  }
}

// ---------- 复盘 / 顺延 ----------
const reviewModal = ref(false)
const reviewTask = ref(null)
function openReview(task) {
  if (isPast.value) return
  reviewTask.value = task
  reviewModal.value = true
}
async function rolloverOne(task, note = '') {
  try {
    await plansStore.rolloverTask(task.id, note)
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '顺延失败'
  }
}
async function confirmRollover(note) {
  if (!reviewTask.value) return
  await rolloverOne(reviewTask.value, note)
  reviewModal.value = false
}
async function rolloverAll() {
  if (isPast.value) return
  for (const task of viewUnfinished.value) {
    await rolloverOne(task)
  }
}
async function reopenTask(task) {
  if (!confirm(`确定把「${task.title}」重新打开，回到今日列表吗？`)) return
  try {
    await plansStore.updateTask(task.id, { completed: false })
    await refresh()
  } catch (e) {
    error.value = e.response?.data?.detail || '重新打开失败'
  }
}

// ---------- 导出 ----------
async function exportWeek() {
  try {
    await plansStore.exportWeek(selectedWeek.value)
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
  <div :class="{ ro: isPast }">
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2">
          <button class="week-nav" title="上一周" @click="moveWeek(-1)">‹</button>
          <p class="whitespace-nowrap text-xs font-semibold tracking-widest text-teal">{{ weekLabel }}</p>
          <button class="week-nav" title="下一周" :disabled="selectedWeek === weekStart" @click="moveWeek(1)">›</button>
          <button v-if="isPast" class="week-text" @click="goThisWeek">回到本周</button>
        </div>
        <span v-if="isPast" class="inline-flex items-center rounded-full border border-amber bg-amber-soft px-2.5 py-0.5 text-[10px] font-bold text-amber">历史周 · 只读</span>
      </div>
      <div class="flex items-center gap-3">
        <span class="inline-flex items-center gap-2 rounded-full border border-hairline bg-card px-3 py-1.5 text-xs text-sub">
          {{ isCurrentWeek ? '本周完成度' : '当周完成度' }} <b class="text-ink">{{ weekStats.pct }}%</b>
          <span class="h-1.5 w-16 overflow-hidden rounded-full bg-hairline">
            <span class="block h-full rounded-full bg-teal" :style="{ width: weekStats.pct + '%' }"></span>
          </span>
        </span>
        <button
          class="rounded-lg border border-hairline bg-card px-3 py-1.5 text-xs font-semibold text-sub hover:border-teal hover:text-teal"
          @click="exportWeek"
        >
          {{ isCurrentWeek ? '导出本周' : '导出当周' }}
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
          { key: 'summary', label: '周总结' },
          { key: 'stat', label: '统计' },
        ]"
        :key="tab.key"
        class="rounded-lg px-4 py-2 text-sm font-medium text-sub hover:bg-paper-soft"
        :class="{ 'bg-card text-teal shadow-sm ring-1 ring-hairline': activeTab === tab.key }"
        @click="selectTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 今日 -->
    <div v-if="activeTab === 'today'">
      <div class="overflow-hidden rounded-lg border border-hairline bg-card shadow-sm">
        <div class="flex items-center justify-between border-b border-hairline px-4 py-3">
          <h3 class="text-sm font-semibold text-ink">{{ todayLabel }}</h3>
          <button class="no-read rounded bg-teal px-3 py-1.5 text-xs font-semibold text-white hover:bg-teal-dark" @click="openTaskModal()">
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
        <div v-if="loaded && !viewUnfinished.length" class="px-4 py-8 text-center text-sm text-sub">{{ isCurrentWeek ? '今天没有待办，点「添加任务」安排一件吧。' : '该周没有任务记录。' }}</div>
        <div
          v-for="task in viewUnfinished"
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
          {{ isCurrentWeek ? '今日进度' : '当周任务' }}
          <b class="text-ink">{{ viewDoneCount }}/{{ viewTasks.length }}</b>
        </div>
      </div>
    </div>

    <!-- 本周计划 -->
    <div v-if="activeTab === 'plan'">
      <div class="mb-4 flex items-center justify-between">
        <div>
          <h3 class="text-base font-semibold">{{ isCurrentWeek ? '本周计划' : '该周计划' }}</h3>
          <p class="text-xs text-sub">{{ isCurrentWeek ? '点计划卡片，右侧管理子任务 · 中途可随时加新计划' : '点计划卡片，右侧查看该计划子任务' }}</p>
        </div>
        <button class="no-read rounded bg-teal px-3 py-1.5 text-xs font-semibold text-white hover:bg-teal-dark" @click="openPlanModal()">＋ 添加计划</button>
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
          <p v-if="loaded && !plans.length" class="rounded-xl border border-dashed border-hairline p-6 text-center text-sm text-sub">{{ isCurrentWeek ? '本周还没有计划，先加一个吧。' : '该周还没有计划。' }}</p>
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
              <button class="no-read rounded-lg border border-hairline px-3 py-1.5 text-xs font-semibold text-sub hover:border-teal hover:text-teal" @click="openPlanModal(selectedPlan)">
                编辑计划
              </button>
              <button class="no-read rounded-lg border border-hairline px-3 py-1.5 text-xs font-semibold text-sub hover:border-red hover:text-red" @click="deletePlan(selectedPlan)">
                删除计划
              </button>
              <button
                class="no-read rounded px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90"
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
          <div v-if="loaded && !selectedPlan.subtasks.length" class="px-4 py-6 text-center text-sm text-sub">{{ isCurrentWeek ? '还没有子任务，点右上角「添加子任务」加一条吧。' : '该计划还没有子任务。' }}</div>
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
            <button class="no-read justify-self-start text-hairline hover:text-red" title="删除子任务" @click.stop="deleteSubtask(sub)">×</button>
          </div>
        </div>
        <div v-else-if="loaded" class="rounded-xl border border-dashed border-hairline p-10 text-center text-sm text-sub">{{ isCurrentWeek ? '从左侧选择一个计划，查看和管理子任务' : '从左侧选择一个计划，查看该计划子任务' }}</div>
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
            <button class="no-read mt-4 rounded-lg border border-hairline px-3 py-1.5 text-xs font-semibold text-sub hover:border-teal hover:text-teal" @click="reopenTask(selectedDone)">
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
          <h4 class="mb-2 text-sm font-semibold text-ink">未完成 · {{ viewUnfinished.length }} 项</h4>
          <div v-for="task in viewUnfinished" :key="task.id" class="flex items-center gap-3 border-t border-dashed border-hairline py-3 text-sm">
            <span class="check-circle" :class="{ on: task.completed }" @click="toggleTask(task)"></span>
            <span class="flex-1 cursor-pointer font-medium text-teal" @click="openReview(task)">{{ task.title }}</span>
            <span v-if="task.plan_title" class="rounded-full bg-paper-soft px-2 py-0.5 text-[11px] text-sub">{{ task.plan_title }}</span>
          </div>
          <p v-if="loaded && !viewUnfinished.length" class="py-6 text-center text-sm text-sub">{{ isCurrentWeek ? '今天都完成了，真棒。' : '该周都完成了。' }}</p>
          <button class="no-read mt-4 w-full rounded-lg bg-teal py-2 text-sm font-semibold text-white hover:bg-teal-dark" @click="rolloverAll">全部顺延到明天</button>
        </div>
        <div class="bg-paper-soft p-5">
          <h4 class="mb-2 text-sm font-semibold text-ink">{{ isCurrentWeek ? '今日回顾' : '该周回顾' }}</h4>
          <div class="flex items-center justify-between border-t border-dashed border-hairline py-2.5 text-sm">
            <span class="text-sub">{{ isCurrentWeek ? '今日完成' : '该周完成' }}</span><b class="text-ink">{{ viewDoneCount }} 项</b>
          </div>
          <div class="flex items-center justify-between border-t border-dashed border-hairline py-2.5 text-sm">
            <span class="text-sub">{{ isCurrentWeek ? '本周完成度' : '该周完成度' }}</span><b class="text-ink">{{ weekStats.pct }}%</b>
          </div>
          <div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-hairline">
            <span class="block h-full rounded-full bg-green" :style="{ width: weekStats.pct + '%' }"></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计（全局视图，不跟随所选周） -->
    <StatsPanel v-if="activeTab === 'stat'" :weeks="statData?.weeks || []" :error="statError" />

    <!-- 周总结（跟随所选周，任何一周都能回顾并修改） -->
    <SummaryPanel v-if="activeTab === 'summary'" :week-start="selectedWeek" />

    <!-- 弹窗 -->
    <PlanModal v-if="planModal" :plan="planEditing" @save="savePlan" @close="planModal = false" />
    <SubtaskModal v-if="subModal" :subtask="subEditing" @save="saveSubtask" @close="subModal = false" />
    <TaskModal v-if="taskModal" :task="taskEditing" :today="today" :plans="plans" @save="saveTask" @delete="deleteTask" @close="taskModal = false" />
    <ReviewModal v-if="reviewModal && reviewTask" :task="reviewTask" @confirm="confirmRollover" @close="reviewModal = false" />
  </div>
</template>

<style scoped>
.week-nav {
  width: 30px;
  height: 30px;
  border: 1px solid var(--hairline);
  background: var(--card);
  color: var(--ink);
  border-radius: 9px;
  cursor: pointer;
  font-size: 17px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: none;
}
.week-nav:hover {
  border-color: var(--teal);
  color: var(--teal);
}
.week-nav:disabled {
  opacity: 0.4;
  cursor: default;
}
.week-text {
  font-size: 12px;
  color: var(--sub);
  border: 1px solid var(--hairline);
  background: var(--card);
  border-radius: 8px;
  padding: 4px 10px;
  cursor: pointer;
  white-space: nowrap;
}
.week-text:hover {
  border-color: var(--teal);
  color: var(--teal);
}
/* 过往周只读：隐藏编辑/新增/删除/顺延入口，勾选圆圈不可点 */
.ro .no-read {
  display: none !important;
}
.ro .check-circle {
  cursor: default;
}
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
  background: var(--hairline);
}
.resize-handle:hover::after {
  background: var(--teal);
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
  background: var(--green);
  border-color: var(--green);
}
.check-circle.on::after {
  content: '✓';
  color: #fff;
  font-size: 12px;
  font-weight: 800;
  line-height: 1;
}
</style>
