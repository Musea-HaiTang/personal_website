<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import api from '../api'

const mode = ref('focus') // focus | break
const state = ref('idle') // idle | running | paused
const focusMinutes = ref(25)
const breakMinutes = ref(5)
const remaining = ref(25 * 60)
const error = ref('')
const summary = ref({ count: 0, total_seconds: 0 })

let timer = null

const totalSeconds = computed(() => (mode.value === 'focus' ? focusMinutes.value : breakMinutes.value) * 60)

const displayTime = computed(() => {
  const m = String(Math.floor(remaining.value / 60)).padStart(2, '0')
  const s = String(remaining.value % 60).padStart(2, '0')
  return `${m}:${s}`
})

const modeLabel = computed(() => (mode.value === 'focus' ? '专注' : '休息'))

function clearTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function stopAndReset() {
  clearTimer()
  state.value = 'idle'
  remaining.value = totalSeconds.value
}

function start() {
  if (state.value === 'idle') remaining.value = totalSeconds.value
  state.value = 'running'
  clearTimer()
  timer = setInterval(tick, 1000)
}

function pause() {
  clearTimer()
  state.value = 'paused'
}

function reset() {
  stopAndReset()
}

function tick() {
  remaining.value -= 1
  if (remaining.value <= 0) {
    complete()
  }
}

async function complete() {
  clearTimer()
  if (mode.value === 'focus') {
    const focusSeconds = remaining.value <= 0 ? totalSeconds.value : totalSeconds.value - remaining.value
    if (focusSeconds > 0) {
      try {
        await api.post('/pomodoro/sessions', { focus_seconds: focusSeconds })
        await loadSummary()
      } catch (e) {
        error.value = e.response?.data?.detail || '记录番茄失败'
      }
    }
  }
  mode.value = mode.value === 'focus' ? 'break' : 'focus'
  stopAndReset()
}

async function loadSummary() {
  try {
    const { data } = await api.get('/pomodoro/sessions')
    summary.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || '加载统计失败'
  }
}

function adjustMinutes(delta) {
  if (state.value !== 'idle') return
  if (mode.value === 'focus') {
    focusMinutes.value = Math.min(120, Math.max(1, focusMinutes.value + delta))
    remaining.value = focusMinutes.value * 60
  } else {
    breakMinutes.value = Math.min(60, Math.max(1, breakMinutes.value + delta))
    remaining.value = breakMinutes.value * 60
  }
}

function switchMode(target) {
  if (state.value === 'running' && !confirm('切换模式会中断当前计时，确定继续？')) return
  mode.value = target
  stopAndReset()
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m === 0) return `${s} 秒`
  return s === 0 ? `${m} 分钟` : `${m} 分 ${s} 秒`
}

onMounted(loadSummary)
onBeforeUnmount(clearTimer)
</script>

<template>
  <div>
    <div class="mb-6 flex items-center justify-between">
      <h2 class="font-serif text-2xl font-bold text-ink">番茄钟</h2>
      <div class="text-sm text-sub">
        今日专注：<span class="font-semibold text-teal">{{ summary.count }}</span> 次 ·
        <span class="font-semibold text-teal">{{ formatDuration(summary.total_seconds) }}</span>
      </div>
    </div>

    <p v-if="error" class="mb-4 rounded bg-red-soft px-3 py-2 text-sm text-red">{{ error }}</p>

    <div class="mx-auto max-w-md rounded-lg border border-hairline bg-card p-8 text-center shadow-sm">
      <div class="mb-4 flex justify-center gap-2">
        <button
          class="rounded px-4 py-1.5 text-sm"
          :class="mode === 'focus' ? 'bg-teal text-white' : 'bg-paper-soft text-sub'"
          @click="switchMode('focus')"
        >
          专注
        </button>
        <button
          class="rounded px-4 py-1.5 text-sm"
          :class="mode === 'break' ? 'bg-green text-white' : 'bg-paper-soft text-sub'"
          @click="switchMode('break')"
        >
          休息
        </button>
      </div>

      <p class="mb-2 text-sm text-sub">{{ modeLabel }}</p>
      <p class="mb-6 text-6xl font-bold tabular-nums" :class="mode === 'focus' ? 'text-teal' : 'text-green'">
        {{ displayTime }}
      </p>

      <div v-if="state === 'idle'" class="mb-6 flex items-center justify-center gap-3 text-sm text-sub">
        <button class="h-8 w-8 rounded-full border border-hairline hover:bg-paper-soft" @click="adjustMinutes(-1)">−</button>
        <span>{{ mode === 'focus' ? focusMinutes : breakMinutes }} 分钟</span>
        <button class="h-8 w-8 rounded-full border border-hairline hover:bg-paper-soft" @click="adjustMinutes(1)">+</button>
      </div>
      <div v-else class="mb-6 text-xs text-sub">
        {{ mode === 'focus' ? focusMinutes : breakMinutes }} 分钟 / 已调整不可改
      </div>

      <div class="flex justify-center gap-3">
        <button
          v-if="state !== 'running'"
          class="rounded bg-teal px-6 py-2 text-white hover:bg-teal-dark"
          @click="start"
        >
          {{ state === 'paused' ? '继续' : '开始' }}
        </button>
        <button v-else class="rounded bg-amber px-6 py-2 text-white hover:bg-amber-dark" @click="pause">暂停</button>
        <button
          v-if="state !== 'idle'"
          class="rounded border border-hairline px-6 py-2 text-sub hover:bg-paper-soft"
          @click="reset"
        >
          重置
        </button>
        <button
          v-if="state !== 'idle' && mode === 'focus'"
          class="rounded border border-green px-6 py-2 text-green hover:bg-green-soft"
          @click="complete"
        >
          完成
        </button>
      </div>
    </div>

    <p class="mt-4 text-center text-xs text-sub">
      专注结束后自动记录本次时长并切换到休息；绑定计划任务将在后续版本提供。
    </p>
  </div>
</template>
