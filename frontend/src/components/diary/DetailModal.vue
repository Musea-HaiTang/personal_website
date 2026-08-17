<script setup>
const props = defineProps({
  item: { type: Object, default: null }
})
const emit = defineEmits(['close', 'delete'])

function plainText(s) {
  return (s || '').replace(/^#+\s*/gm, '')
}
</script>

<template>
  <div class="detail-overlay" @click.self="emit('close')">
    <div class="detail-card" :class="{ flash: item.kind === 'flash' }">
      <div class="d-head">
        <h4 class="d-title">{{ item.kind === 'flash' ? '闪念' : (item.title || '无标题') }}</h4>
        <div class="d-date">{{ item.label }}</div>
      </div>
      <div v-if="item.tags && item.tags.length" class="d-tags">
        <span v-for="t in item.tags" :key="t" class="tag">{{ t }}</span>
      </div>
      <div class="d-body">{{ plainText(item.full) }}</div>
      <div class="d-actions">
        <button type="button" class="btn danger" @click="emit('delete')">删除</button>
        <button type="button" class="btn" @click="emit('close')">关闭</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.detail-overlay {
  position: fixed;
  inset: 0;
  background: rgba(43, 38, 34, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 60;
  padding: 24px;
}
.btn {
  border: 1px solid var(--hairline);
  background: var(--card);
  color: var(--ink);
  border-radius: 8px;
  padding: 7px 12px;
  font-size: 13px;
  cursor: pointer;
}
.btn:hover {
  border-color: var(--teal);
  color: var(--teal);
}
.btn.danger {
  color: var(--red);
  border-color: var(--red);
}
.tag {
  background: var(--paper-soft);
  color: var(--sub);
  border-radius: 999px;
  padding: 2px 9px;
  font-size: 12px;
}
.detail-card {
  width: min(460px, 100%);
  max-height: 82vh;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  box-shadow: 0 24px 70px rgba(43, 38, 34, 0.4);
  position: relative;
  font-family: var(--kai);
  background: #fdfbf7;
  border: 1px solid var(--hairline);
}
.detail-card.flash {
  background: var(--amber-soft);
  border: 1px solid var(--amber-line);
  border-radius: 5px;
  box-shadow: 4px 6px 14px rgba(43, 38, 34, 0.15);
  font-family: "Songti SC", "STSong", SimSun, serif;
}
.detail-card.flash::before {
  content: "";
  position: absolute;
  top: -9px;
  left: 50%;
  transform: translateX(-50%) rotate(1deg);
  width: 76px;
  height: 16px;
  background: rgba(255, 255, 255, 0.5);
  border: 1px solid var(--amber-line);
  border-bottom: none;
  border-radius: 3px 3px 0 0;
  z-index: 2;
}
.d-head {
  position: relative;
  padding: 18px 24px 12px;
}
.detail-card.flash .d-head {
  padding-top: 22px;
}
.d-head::after {
  content: "记";
  position: absolute;
  top: 12px;
  right: 20px;
  width: 26px;
  height: 26px;
  background: var(--teal);
  color: #fff;
  font-family: "Songti SC", "STSong", SimSun, serif;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 5px;
  transform: rotate(-4deg);
  box-shadow: 0 1px 2px rgba(43, 38, 34, 0.18);
  line-height: 1;
}
.detail-card.flash .d-head::after {
  display: none;
}
.d-title {
  font-size: 19px;
  font-weight: 700;
  margin: 0 0 4px;
  padding-right: 44px;
}
.detail-card.flash .d-title {
  color: var(--amber);
}
.d-date {
  font-size: 12px;
  color: var(--sub);
}
.detail-card.flash .d-date {
  color: var(--amber);
}
.d-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding: 8px 24px 10px;
}
.d-tags .tag {
  background: var(--teal-soft);
  color: var(--teal);
  border: 1px solid var(--teal);
}
.detail-card.flash .d-tags .tag {
  background: rgba(255, 255, 255, 0.6);
  color: var(--amber);
  border-color: var(--amber-line);
}
.d-body {
  flex: 1;
  overflow: auto;
  padding: 8px 24px 18px;
  white-space: pre-wrap;
  line-height: 1.9;
  font-size: 15px;
  min-height: 260px;
  background: repeating-linear-gradient(to bottom, transparent 0 29px, #ece7da 29px 30px);
}
.detail-card.flash .d-body {
  background: none;
  font-size: 17px;
  min-height: 240px;
}
.d-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  align-items: center;
  padding: 12px 22px;
  border-top: 1px dashed var(--hairline);
}
.detail-card.flash .d-actions {
  border-top-color: var(--amber-line);
}
</style>
