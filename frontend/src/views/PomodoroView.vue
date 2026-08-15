<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import { MODES, usePomodoroStore } from '../stores/pomodoro'

const store = usePomodoroStore()
const popoverOpen = ref(false)
const editing = ref(false)
const timeInput = ref(null)

const ringC = 2 * Math.PI * 128
const leafPath = 'M0,0 C12,-10 28,-10 36,0 C28,10 12,10 0,0 Z'
const leaves = [
  { transform: 'translate(160,16) rotate(8)' },
  { transform: 'translate(304,160) rotate(98)' },
  { transform: 'translate(160,304) rotate(188)' },
  { transform: 'translate(16,160) rotate(278)' }
]

function enterEdit() {
  if (store.running || store.paused) return
  editing.value = true
  nextTick(() => timeInput.value?.focus())
}

function applyEdit() {
  if (!editing.value) return
  const v = (timeInput.value?.value || '').trim()
  if (v) {
    let mins
    if (v.includes(':')) {
      const p = v.split(':')
      mins = (parseInt(p[0], 10) || 0) + (parseInt(p[1], 10) || 0) / 60
    } else {
      mins = parseFloat(v)
    }
    if (Number.isFinite(mins) && mins > 0) store.setMinutes(mins)
  }
  editing.value = false
}

function onEditKey(e) {
  if (e.key === 'Enter') {
    applyEdit()
  } else if (e.key === 'Escape') {
    editing.value = false
  }
}

function fmtSessionTime(iso) {
  const d = new Date(iso)
  return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0')
}

function fmtDuration(sec) {
  return sec >= 60 ? Math.round(sec / 60) + ' 分钟' : sec + ' 秒'
}

function onDocClick() {
  popoverOpen.value = false
}

onMounted(() => {
  store.loadToday()
  document.addEventListener('click', onDocClick)
})

onBeforeUnmount(() => document.removeEventListener('click', onDocClick))
</script>

<template>
  <div>
    <div class="mb-6 flex items-start justify-between gap-4">
      <div>
        <h2 class="font-serif text-2xl font-bold text-ink">番茄钟</h2>
        <p class="mt-1 text-sm text-sub">藤蔓绕着时间生长</p>
      </div>
      <div class="relative">
        <button class="today-stats" type="button" @click.stop="popoverOpen = !popoverOpen">
          今日 <b>{{ store.count }}</b> 个 🍅 · <b>{{ store.totalMin }}</b> 分钟
          <span class="caret">▾</span>
        </button>
        <div v-if="popoverOpen" class="popover" @click.stop>
          <div class="pop-head">
            <h3 class="font-serif text-[15px] font-bold">今日专注</h3>
            <button class="pop-close" type="button" @click="popoverOpen = false">×</button>
          </div>
          <div v-if="store.sessions.length" class="logs">
            <div v-for="s in store.sessions" :key="s.id" class="logrow">
              <span class="logt">{{ fmtSessionTime(s.started_at) }}</span>
              <span class="logdot" />
              <span class="logl">专注 {{ fmtDuration(s.focus_seconds) }}</span>
            </div>
          </div>
          <p v-else class="empty-tip">今天还没有专注记录，点开始种下第一颗 🍅</p>
        </div>
      </div>
    </div>

    <p v-if="store.error" class="mb-4 rounded bg-red-soft px-3 py-2 text-sm text-red">{{ store.error }}</p>

    <div class="ring-card">
      <div class="modetabs">
        <button
          v-for="m in ['focus', 'break']"
          :key="m"
          type="button"
          class="modebtn"
          :class="{ active: store.mode === m, [m]: true }"
          @click="store.setMode(m)"
        >
          {{ MODES[m].label }}
        </button>
      </div>

      <div class="ring">
        <svg viewBox="0 0 320 320" width="300" height="300">
          <circle class="ring-bg" cx="160" cy="160" r="128" />
          <circle
            class="ring-prog"
            :style="{
              strokeDasharray: ringC,
              strokeDashoffset: ringC * (1 - store.progress),
              stroke: MODES[store.mode].hex
            }"
            cx="160"
            cy="160"
            r="128"
          />
          <circle class="ring-vine" cx="160" cy="160" r="144" />
          <g>
            <animateTransform
              attributeName="transform"
              type="rotate"
              from="0 160 160"
              to="360 160 160"
              dur="45s"
              repeatCount="indefinite"
            />
            <g v-for="(leaf, i) in leaves" :key="i" :transform="leaf.transform">
              <path :d="leafPath" fill="#7fb069" opacity=".5" />
            </g>
          </g>
        </svg>
        <div class="ring-time">
          <div class="time-edit" title="点击修改时长" @click="enterEdit">
            <span v-if="!editing" class="t-time" :class="store.mode">{{ store.fmtTime }}</span>
            <input
              v-else
              ref="timeInput"
              class="t-edit"
              inputmode="numeric"
              autocomplete="off"
              spellcheck="false"
              :placeholder="String(store.modeMin)"
              aria-label="输入分钟数"
              @keydown="onEditKey"
              @blur="applyEdit"
            >
            <span class="edit-hint" aria-hidden="true">✎</span>
            <span v-if="editing" class="t-unit">分钟</span>
          </div>
        </div>
      </div>

      <div class="controls">
        <button
          class="icon-btn primary"
          :class="{ playing: store.running }"
          type="button"
          :title="store.running ? '暂停' : '开始'"
          aria-label="开始或暂停"
          @click="store.startPause()"
        >
          <svg v-if="!store.running" class="ic ic-play" viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15l13-7.5z" /></svg>
          <svg v-else class="ic ic-pause" viewBox="0 0 24 24" fill="currentColor"><path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z" /></svg>
        </button>
        <button
          class="icon-btn ghost"
          :class="{ disabled: !store.running && !store.paused }"
          type="button"
          title="重置"
          aria-label="重置"
          @click="store.reset()"
        >
          <svg class="ic" viewBox="0 0 24 24" fill="currentColor"><rect x="5.5" y="5.5" width="13" height="13" rx="2" /></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.today-stats {
  background: #fffefc;
  border: 1px solid #e9e3d9;
  border-radius: 12px;
  padding: 10px 16px;
  font-size: 14px;
  color: #7c7468;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  transition: 0.15s;
}
.today-stats:hover {
  border-color: #0e7c74;
  box-shadow: 0 4px 14px rgba(14, 124, 116, 0.1);
}
.today-stats b {
  color: #0e7c74;
  font-size: 18px;
}
.caret {
  font-size: 11px;
  color: #7c7468;
  margin-left: 2px;
}
.popover {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  width: 320px;
  max-width: 86vw;
  background: #fffefc;
  border: 1px solid #e9e3d9;
  border-radius: 14px;
  box-shadow: 0 14px 36px rgba(43, 38, 34, 0.16);
  padding: 12px 14px;
  z-index: 30;
}
.pop-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.pop-close {
  border: 0;
  background: #f4f1ea;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  color: #7c7468;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
}
.pop-close:hover {
  background: #e9e3d9;
  color: #2b2622;
}
.logs {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 240px;
  overflow: auto;
}
.logrow {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  padding: 8px 10px;
  border: 1px dashed #e9e3d9;
  border-radius: 10px;
}
.logt {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 12px;
  color: #7c7468;
}
.logdot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #c4533a;
  flex: none;
}
.logl {
  color: #2b2622;
}
.empty-tip {
  font-size: 13px;
  color: #7c7468;
  padding: 8px 4px;
}
.ring-card {
  max-width: 560px;
  margin: 0 auto;
  background: #fffefc;
  border: 1px solid #e9e3d9;
  border-radius: 18px;
  box-shadow: 0 6px 24px rgba(43, 38, 34, 0.06);
  text-align: center;
  padding: 28px 24px 26px;
}
.modetabs {
  display: flex;
  justify-content: center;
  gap: 4px;
  background: #f4f1ea;
  border: 1px solid #e9e3d9;
  border-radius: 999px;
  padding: 4px;
  margin: 0 auto 10px;
  width: max-content;
}
.modebtn {
  border: 0;
  background: transparent;
  padding: 7px 18px;
  border-radius: 999px;
  font-size: 14px;
  color: #7c7468;
  cursor: pointer;
  transition: 0.2s;
}
.modebtn:hover {
  color: #2b2622;
}
.modebtn.active.focus {
  background: #0e7c74;
  color: #fff;
}
.modebtn.active.break {
  background: #3d9970;
  color: #fff;
}
.ring {
  position: relative;
  width: 300px;
  height: 300px;
  margin: 6px auto;
}
.ring svg {
  display: block;
  width: 100%;
  height: 100%;
}
.ring-bg {
  fill: none;
  stroke: #e9e3d9;
  stroke-width: 14;
}
.ring-prog {
  fill: none;
  stroke: #0e7c74;
  stroke-width: 14;
  stroke-linecap: round;
  transform: rotate(-90deg);
  transform-origin: center;
  transition: stroke-dashoffset 1s linear, stroke 0.4s;
}
.ring-vine {
  fill: none;
  stroke: #c9c1b2;
  stroke-dasharray: 4 10;
  stroke-width: 2;
}
.ring-time {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}
.time-edit {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: text;
}
.t-time {
  font-family: "Songti SC", "STSong", "SimSun", serif;
  font-size: 58px;
  font-weight: 700;
  letter-spacing: 0.02em;
  line-height: 1.05;
  transition: color 0.4s;
}
.t-time.focus {
  color: #0e7c74;
}
.t-time.break {
  color: #3d9970;
}
.edit-hint {
  position: absolute;
  left: calc(100% + 6px);
  top: 50%;
  transform: translateY(-50%);
  font-size: 15px;
  color: #7c7468;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
  line-height: 1;
}
.time-edit:hover .edit-hint {
  opacity: 1;
}
.t-edit {
  font-family: "Songti SC", "STSong", "SimSun", serif;
  font-size: 52px;
  font-weight: 700;
  text-align: center;
  width: 3ch;
  border: 0;
  border-bottom: 2px dashed #0e7c74;
  background: transparent;
  outline: none;
  caret-color: #0e7c74;
  color: #2b2622;
  padding: 0 2px;
  line-height: 1.05;
}
.t-edit::selection {
  background: #e7f1ef;
}
.t-unit {
  font-size: 14px;
  color: #7c7468;
  margin-left: 2px;
}
.controls {
  display: flex;
  gap: 14px;
  justify-content: center;
  margin-top: 18px;
}
.icon-btn {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  border: 1px solid transparent;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: 0.15s;
}
.icon-btn .ic {
  width: 22px;
  height: 22px;
}
.icon-btn.primary {
  background: #0e7c74;
  color: #fff;
}
.icon-btn.primary:hover {
  background: #0a6a63;
}
.icon-btn.primary.playing {
  background: #b7791f;
}
.icon-btn.ghost {
  border-color: #e9e3d9;
  color: #7c7468;
  background: #fffefc;
}
.icon-btn.ghost:hover {
  background: #f4f1ea;
}
.icon-btn.disabled {
  opacity: 0.45;
  cursor: not-allowed;
  pointer-events: none;
  background: #f4f1ea;
  border-color: #e9e3d9;
  border-style: dashed;
  color: #7c7468;
}
</style>
