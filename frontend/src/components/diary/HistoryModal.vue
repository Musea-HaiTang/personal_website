<script setup>
import { computed, ref } from 'vue'

import { useDiaryStore } from '../../stores/diary'

const emit = defineEmits(['close', 'open-detail'])

const diaryStore = useDiaryStore()

const histTab = ref('all')
const histQuery = ref('')

function fmtDate(d) {
  const [y, m, dd] = d.split('-')
  return `${y}.${m}.${dd}`
}
function strip(s) {
  return (s || '').replace(/\s+/g, ' ').trim()
}

const histItems = computed(() => {
  const items = []
  diaryStore.entries.forEach((e) =>
    items.push({ id: e.id, kind: 'diary', sort: e.date + 'T00:00:00', label: fmtDate(e.date), title: e.title, tags: e.tags, excerpt: strip(e.content), full: e.content })
  )
  diaryStore.flashes.forEach((f) => {
    const s = String(f.created_at)
    items.push({ id: f.id, kind: 'flash', sort: s, label: s.slice(5, 10).replace('-', '/') + ' ' + s.slice(11, 16), title: f.content, full: f.content })
  })
  return items.sort((a, b) => b.sort.localeCompare(a.sort))
})

const filteredHist = computed(() => {
  const q = histQuery.value.trim().toLowerCase()
  return histItems.value.filter(
    (it) =>
      (histTab.value === 'all' || it.kind === histTab.value) &&
      (!q || (it.title + ' ' + (it.excerpt || '') + ' ' + (it.tags || []).join(' ')).toLowerCase().includes(q))
  )
})
</script>

<template>
  <div class="overlay" @click.self="emit('close')">
    <div class="modal">
      <div class="m-head">
        <h3>往日记录</h3>
        <button type="button" class="btn" @click="emit('close')">关闭</button>
      </div>
      <div class="tabs">
        <button v-for="k in [['all', '全部'], ['diary', '日记'], ['flash', '闪念']]" :key="k[0]" type="button" class="tab" :class="{ active: histTab === k[0] }" @click="histTab = k[0]">{{ k[1] }}</button>
      </div>
      <div class="m-body">
        <input v-model="histQuery" class="search" placeholder="搜索标题 / 标签 / 内容…">
        <div class="timeline">
          <div v-for="(it, i) in filteredHist" :key="i" class="tl" :class="{ flash: it.kind === 'flash' }" @click="emit('open-detail', it)">
            <span class="when">{{ it.label }}</span>
            <div class="body">
              <div class="tt">{{ it.title }}</div>
              <div v-if="it.excerpt" class="ex">{{ it.excerpt }}</div>
              <div v-if="it.tags && it.tags.length" class="tags-row"><span v-for="t in it.tags" :key="t" class="tag">{{ t }}</span></div>
            </div>
            <span class="kind">{{ it.kind === 'flash' ? '闪念' : '日记' }}</span>
          </div>
          <p v-if="!filteredHist.length" class="none">没有符合条件的记录</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  align-items: flex-start;
  padding-top: 7vh;
}
.modal {
  box-shadow: 0 20px 60px rgba(43, 38, 34, 0.32);
  width: min(780px, 100%);
  max-height: 84vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.m-head {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  border-bottom: 1px solid var(--hairline);
}
.m-head h3 {
  font-family: "Songti SC", "STSong", SimSun, serif;
  font-size: 18px;
  font-weight: 700;
  margin: 0;
  margin-right: auto;
}
.tabs {
  display: flex;
  gap: 8px;
  padding: 12px 20px 0;
}
.tab {
  border: 1px solid var(--hairline);
  background: var(--card);
  color: var(--sub);
  border-radius: 999px;
  padding: 5px 14px;
  font-size: 13px;
  cursor: pointer;
}
.tab.active {
  background: var(--teal);
  border-color: var(--teal);
  color: #fff;
}
.m-body {
  flex: 1;
  overflow: auto;
  padding: 14px 20px 20px;
}
.search {
  width: 100%;
  border: 1px solid var(--hairline);
  border-radius: 8px;
  background: var(--card);
  padding: 8px 12px;
  font-size: 13px;
  outline: none;
  margin-bottom: 12px;
}
.search:focus {
  border-color: var(--teal);
}
.timeline {
  display: flex;
  flex-direction: column;
  gap: 9px;
}
.tl {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 10px;
  padding: 11px 14px;
  cursor: pointer;
  transition: border-color 0.12s, box-shadow 0.12s;
}
.tl:hover {
  border-color: var(--teal);
  box-shadow: 0 3px 10px rgba(43, 38, 34, 0.08);
}
.tl.flash {
  background: var(--amber-soft);
  border-color: var(--amber-line);
  transform: rotate(-0.25deg);
}
.tl.flash:hover {
  border-color: var(--amber);
}
.tl .when {
  width: 86px;
  flex-shrink: 0;
  font-size: 12px;
  color: var(--sub);
  padding-top: 2px;
}
.tl .body {
  flex: 1;
  min-width: 0;
  padding: 0;
  background: none;
  line-height: 1.6;
}
.tl .body .tt {
  font-size: 14px;
  font-weight: 600;
}
.tl .body .ex {
  font-size: 13px;
  color: var(--sub);
  margin-top: 2px;
}
.tl .kind {
  font-size: 11px;
  color: var(--teal);
  background: var(--teal-soft);
  border-radius: 999px;
  padding: 1px 8px;
  flex-shrink: 0;
}
.tl.flash .kind {
  color: var(--amber);
  background: rgba(255, 255, 255, 0.6);
}
.tags-row {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
  margin-top: 5px;
}
.none {
  color: var(--sub);
  font-size: 13px;
  text-align: center;
  padding: 24px 0;
}
</style>
