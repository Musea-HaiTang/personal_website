import { defineStore } from 'pinia'

import api from '../api'
import { localDateStr } from '../utils/date'

export const MODES = {
  focus: { label: '专注', sec: 25 * 60, hex: '#0e7c74' },
  break: { label: '休息', sec: 5 * 60, hex: '#3d9970' }
}

let timerId = null

export const usePomodoroStore = defineStore('pomodoro', {
  state: () => ({
    mode: 'focus',
    running: false,
    paused: false,
    totalSec: MODES.focus.sec,
    remainingSec: MODES.focus.sec,
    endAt: null,
    miniHidden: false,
    count: 0,
    totalSeconds: 0,
    sessions: [],
    tasks: [],
    taskId: null,
    error: '',
    toastMsg: '',
    toastSeq: 0
  }),
  getters: {
    progress() {
      return this.totalSec > 0 ? 1 - this.remainingSec / this.totalSec : 1
    },
    modeLabel() {
      return MODES[this.mode].label
    },
    modeMin() {
      return MODES[this.mode].sec / 60
    },
    totalMin() {
      return Math.round(this.totalSeconds / 60)
    },
    fmtTime() {
      const s = Math.max(0, this.remainingSec)
      return String(Math.floor(s / 60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0')
    }
  },
  actions: {
    _clearTimer() {
      if (timerId !== null) {
        clearInterval(timerId)
        timerId = null
      }
    },
    _toast(msg) {
      this.toastMsg = msg
      this.toastSeq += 1
    },
    async loadToday() {
      this.error = ''
      try {
        const { data } = await api.get('/pomodoro/sessions', { params: { day: localDateStr() } })
        this.count = data.count
        this.totalSeconds = data.total_seconds
        this.sessions = data.sessions
      } catch (e) {
        this.error = e.response?.data?.detail || '加载今日统计失败'
      }
    },
    async loadTasks() {
      try {
        const { data } = await api.get('/tasks', { params: { date: localDateStr() } })
        this.tasks = data.filter((t) => !t.completed)
        if (this.taskId && !this.tasks.some((t) => t.id === this.taskId)) this.taskId = null
      } catch (e) {
        this.error = e.response?.data?.detail || '加载今日任务失败'
      }
    },
    setMode(m) {
      if (!MODES[m]) return
      this._clearTimer()
      this.mode = m
      this.totalSec = MODES[m].sec
      this.remainingSec = this.totalSec
      this.running = false
      this.paused = false
      this.endAt = null
    },
    startPause() {
      if (this.running) {
        this._clearTimer()
        this.remainingSec = Math.max(0, Math.round((this.endAt - Date.now()) / 1000))
        this.running = false
        this.paused = true
        this.endAt = null
        return
      }
      this.running = true
      this.paused = false
      this.miniHidden = false
      this.endAt = Date.now() + this.remainingSec * 1000
      timerId = setInterval(() => this._tick(), 1000)
    },
    _tick() {
      const rem = Math.max(0, Math.round((this.endAt - Date.now()) / 1000))
      this.remainingSec = rem
      if (rem <= 0) this.complete()
    },
    reset() {
      this._clearTimer()
      this.remainingSec = this.totalSec
      this.running = false
      this.paused = false
      this.endAt = null
    },
    setMinutes(mins) {
      if (this.running || this.paused) return
      const max = this.mode === 'focus' ? 120 : 60
      const m = Math.min(max, Math.max(1, mins))
      this.totalSec = Math.round(m * 60)
      this.remainingSec = this.totalSec
    },
    async complete() {
      this._clearTimer()
      if (this.mode === 'focus') {
        const elapsed = this.remainingSec > 0 ? this.totalSec - this.remainingSec : this.totalSec
        const sec = Math.max(1, Math.round(elapsed))
        try {
          const { data } = await api.post('/pomodoro/sessions', { focus_seconds: sec, task_id: this.taskId || null })
          this.count += 1
          this.totalSeconds += sec
          this.sessions.unshift(data)
          this._toast('收获一颗番茄 🍅')
        } catch (e) {
          this.error = e.response?.data?.detail || '记录番茄失败'
        }
        this.mode = 'break'
      } else {
        this._toast('休息结束，开始专注吧')
        this.mode = 'focus'
      }
      this.totalSec = MODES[this.mode].sec
      this.remainingSec = this.totalSec
      this.running = false
      this.paused = false
      this.endAt = null
    }
  }
})
