<script setup>
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import { MODES, usePomodoroStore } from '../stores/pomodoro'

const store = usePomodoroStore()
const router = useRouter()

const ringC = 2 * Math.PI * 22
const toastVisible = ref(false)
let toastTimer = null

watch(
  () => store.toastSeq,
  () => {
    toastVisible.value = false
    requestAnimationFrame(() => {
      toastVisible.value = true
    })
    clearTimeout(toastTimer)
    toastTimer = setTimeout(() => {
      toastVisible.value = false
    }, 2200)
  }
)

function onChipClick(e) {
  if (e.target.closest('button')) return
  router.push('/pomodoro')
}
</script>

<template>
  <Transition name="mini">
    <div
      v-if="(store.running || store.paused) && !store.miniHidden"
      class="mini"
      title="回到番茄钟"
      @click="onChipClick"
    >
      <div class="mini-ring">
        <svg viewBox="0 0 52 52">
          <circle class="mini-bg" cx="26" cy="26" r="22" />
          <circle
            class="mini-prog"
            :style="{
              strokeDasharray: ringC,
              strokeDashoffset: ringC * (1 - store.progress),
              stroke: MODES[store.mode].hex
            }"
            cx="26"
            cy="26"
            r="22"
          />
        </svg>
        <span class="mini-time">{{ store.fmtTime }}</span>
      </div>
      <div class="mini-meta">
        <span class="mini-label">{{ store.modeLabel }}</span>
        <div class="mini-actions">
          <button
            class="mini-btn"
            :class="{ playing: store.running }"
            type="button"
            title="暂停/继续"
            aria-label="暂停或继续"
            @click.stop="store.startPause()"
          >
            <svg v-if="!store.running" class="ic ic-play" viewBox="0 0 24 24" fill="currentColor"><path d="M7 4.5v15l13-7.5z" /></svg>
            <svg v-else class="ic ic-pause" viewBox="0 0 24 24" fill="currentColor"><path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z" /></svg>
          </button>
          <button
            class="mini-btn mini-close"
            type="button"
            title="收起"
            aria-label="收起"
            @click.stop="store.miniHidden = true"
          >
            ×
          </button>
        </div>
      </div>
    </div>
  </Transition>

  <Transition name="toast">
    <div v-if="toastVisible && store.toastMsg" class="timer-toast">{{ store.toastMsg }}</div>
  </Transition>
</template>

<style scoped>
.mini {
  position: fixed;
  right: 18px;
  bottom: 18px;
  background: #e7f1ec;
  border: 1px solid #c9e2d5;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(61, 153, 112, 0.18);
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 70;
  cursor: pointer;
}
.mini-ring {
  position: relative;
  width: 52px;
  height: 52px;
  flex: none;
}
.mini-ring svg {
  display: block;
  width: 100%;
  height: 100%;
}
.mini-bg {
  fill: none;
  stroke: #cfe6d8;
  stroke-width: 4;
}
.mini-prog {
  fill: none;
  stroke: #3d9970;
  stroke-width: 4;
  stroke-linecap: round;
  transform: rotate(-90deg);
  transform-origin: center;
  transition: stroke-dashoffset 1s linear, stroke 0.4s;
}
.mini-time {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: ui-monospace, Consolas, monospace;
  font-size: 12px;
  color: #3d9970;
}
.mini-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.mini-label {
  font-size: 12px;
  color: #5d8f76;
}
.mini-actions {
  display: flex;
  gap: 6px;
}
.mini-btn {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  border: 1px solid #c9e2d5;
  background: #fff;
  color: #2b2622;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.mini-btn:hover {
  background: #f4faf7;
}
.mini-btn .ic {
  width: 14px;
  height: 14px;
}
.mini-close {
  color: #7c7468;
}
.mini-enter-active,
.mini-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.mini-enter-from,
.mini-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
.timer-toast {
  position: fixed;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  background: #fffefc;
  border: 1px solid #e9e3d9;
  box-shadow: 0 8px 24px rgba(43, 38, 34, 0.14);
  border-radius: 999px;
  padding: 10px 20px;
  font-size: 14px;
  color: #2b2622;
  z-index: 80;
}
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.25s, transform 0.25s;
}
.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-14px);
}
</style>
