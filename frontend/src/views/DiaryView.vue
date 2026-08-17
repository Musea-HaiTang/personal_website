<script setup>
import { computed, onMounted, ref } from 'vue'

import DetailModal from '../components/diary/DetailModal.vue'
import DiaryEditorModal from '../components/diary/DiaryEditorModal.vue'
import HistoryModal from '../components/diary/HistoryModal.vue'
import { useDiaryStore } from '../stores/diary'

const diaryStore = useDiaryStore()
const entries = computed(() => diaryStore.entries)
const flashes = computed(() => diaryStore.flashes)
const loading = ref(false)
const saving = ref(false)
const error = ref('')

function todayStr() {
  const now = new Date()
  const offset = now.getTimezoneOffset()
  return new Date(now.getTime() - offset * 60000).toISOString().slice(0, 10)
}
const today = todayStr()

function isoOf(d) {
  const p = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate())
}
function strip(s) {
  return (s || '').replace(/\s+/g, ' ').trim()
}
function timeOf(ts) {
  return String(ts).slice(11, 16)
}

const dateLabel = computed(() => {
  const d = new Date(today + 'T00:00:00')
  return `${d.getMonth() + 1}月${d.getDate()}日 · 星期${'日一二三四五六'[d.getDay()]}`
})

const todayDiary = computed(() => entries.value.find((e) => e.date === today) || null)
const todayFlashes = computed(() => flashes.value.filter((f) => String(f.created_at).slice(0, 10) === today))
const todayTags = computed(() => todayDiary.value?.tags || [])
const excerpt = computed(() => strip(todayDiary.value?.content))

const stats = computed(() => {
  const total = entries.value.length
  const words = entries.value.reduce((s, e) => s + (e.content || '').replace(/\s/g, '').length, 0)
  const year = entries.value.filter((e) => e.date.startsWith(String(new Date().getFullYear()))).length
  return { total, words, year }
})

const streak = computed(() => {
  const days = new Set()
  entries.value.forEach((e) => days.add(e.date))
  flashes.value.forEach((f) => days.add(String(f.created_at).slice(0, 10)))
  let n = 0
  const d = new Date(today + 'T12:00:00')
  if (!days.has(today)) d.setDate(d.getDate() - 1)
  while (days.has(isoOf(d))) {
    n++
    d.setDate(d.getDate() - 1)
  }
  return n
})

const heatCells = computed(() => {
  const counts = {}
  entries.value.forEach((e) => (counts[e.date] = (counts[e.date] || 0) + 1))
  flashes.value.forEach((f) => {
    const k = String(f.created_at).slice(0, 10)
    counts[k] = (counts[k] || 0) + 1
  })
  const cells = []
  const start = new Date(today + 'T00:00:00')
  start.setDate(start.getDate() - 25 * 7)
  for (let w = 0; w < 26; w++) {
    for (let dw = 0; dw < 7; dw++) {
      const d = new Date(start)
      d.setDate(start.getDate() + w * 7 + dw)
      const key = isoOf(d)
      const c = counts[key] || 0
      cells.push({ cls: c === 0 ? 'c0' : c === 1 ? 'c1' : c === 2 ? 'c2' : c === 3 ? 'c3' : 'c4', title: `${key}：${c} 条记录` })
    }
  }
  return cells
})

const monthBars = computed(() => {
  const now = new Date(today + 'T00:00:00')
  const months = []
  for (let i = 5; i >= 0; i--) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1)
    const key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0')
    let words = 0
    let count = 0
    entries.value.forEach((e) => {
      if (e.date.startsWith(key)) words += (e.content || '').replace(/\s/g, '').length
    })
    flashes.value.forEach((f) => {
      if (String(f.created_at).slice(0, 7) === key) count++
    })
    months.push({ label: d.getMonth() + 1 + '月', words, count })
  }
  const max = Math.max(...months.map((m) => m.words), 1)
  return months.map((m) => ({ ...m, wordsPct: Math.round((m.words / max) * 100), flashPct: Math.min(100, Math.round((m.count / 20) * 100)) }))
})

const tagTop = computed(() => {
  const tally = {}
  entries.value.forEach((e) => (e.tags || []).forEach((t) => (tally[t] = (tally[t] || 0) + 1)))
  const top = Object.entries(tally).sort((a, b) => b[1] - a[1]).slice(0, 6)
  const max = top.length ? top[0][1] : 1
  return top.map(([name, count]) => ({ name, count, pct: Math.round((count / max) * 100) }))
})

async function loadAll() {
  loading.value = true
  error.value = ''
  await diaryStore.refresh()
  error.value = diaryStore.error
  loading.value = false
}

/* ---------- 编辑弹窗编排 ---------- */
const showEdit = ref(false)
function openEdit() {
  showEdit.value = true
}
function closeEdit() {
  showEdit.value = false
}
async function saveEdit(payload) {
  saving.value = true
  error.value = ''
  try {
    await diaryStore.saveDiary(payload, todayDiary.value?.id ?? null)
    showEdit.value = false
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存日记失败'
  } finally {
    saving.value = false
  }
}
async function deleteDiary() {
  if (!todayDiary.value) return
  if (!confirm('确定删除今天的日记？正文文件也会被删除。')) return
  try {
    await diaryStore.deleteDiary(todayDiary.value.id)
    showEdit.value = false
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除日记失败'
  }
}

/* ---------- 闪念 ---------- */
const flashInput = ref('')

async function addFlash() {
  const v = flashInput.value.trim()
  if (!v) return
  error.value = ''
  try {
    await diaryStore.createFlash(v)
    flashInput.value = ''
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || '记录灵感失败'
  }
}

async function removeFlash(id) {
  try {
    await diaryStore.deleteFlash(id)
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除灵感失败'
  }
}

/* ---------- 往日记录 / 详情 ---------- */
const showHistory = ref(false)
const showDetail = ref(false)
const detailItem = ref(null)

function openDetail(it) {
  detailItem.value = it
  showDetail.value = true
}
function closeDetail() {
  showDetail.value = false
  detailItem.value = null
}
async function deleteDetail() {
  const it = detailItem.value
  if (!it) return
  const msg = it.kind === 'flash' ? '确定删除这条闪念吗？' : '确定删除这篇日记吗？正文文件也会被删除。'
  if (!confirm(msg)) return
  try {
    if (it.kind === 'flash') await diaryStore.deleteFlash(it.id)
    else await diaryStore.deleteDiary(it.id)
    closeDetail()
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除记录失败'
  }
}

/* ---------- 去年今天 ---------- */
const showOtd = ref(false)
const otdEntry = computed(() => {
  const [y, m, d] = today.split('-').map(Number)
  const key = `${y - 1}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
  return entries.value.find((e) => e.date === key) || null
})

onMounted(() => {
  if (!diaryStore.loaded) loadAll()
})
</script>

<template>
  <div class="diary-page">
    <div class="topbar">
      <h2>日记</h2>
      <div class="otd-wrap">
        <button class="btn" @click="showOtd = !showOtd">📬 去年今天</button>
        <div v-if="showOtd" class="otd-pop">
          <template v-if="otdEntry">
            <div class="otd-date">去年今天 · {{ otdEntry.date }}</div>
            <h4>{{ otdEntry.title }}</h4>
            <p>{{ strip(otdEntry.content).slice(0, 80) }}</p>
          </template>
          <template v-else>
            <div class="otd-date">去年今天 · {{ Number(today.split('-')[0]) - 1 }} 年</div>
            <p>去年今天没有记录。坚持写下去，明年这时候就会收到回信。</p>
          </template>
        </div>
      </div>
      <button class="btn" @click="showHistory = true">📚 往日记录</button>
      <span class="streak">已连续记录 <b>{{ streak }}</b> 天</span>
    </div>

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="loading" class="loading">加载中…</p>

    <div class="hero">
      <div class="paper letter clickable" @click="openEdit">
        <div class="head page-head">
          <div class="page-title">{{ todayDiary?.title || '' }}</div>
          <div class="date">{{ dateLabel }}</div>
        </div>
        <div class="page-tags">
          <span v-for="t in todayTags" :key="t" class="tag-chip">{{ t }}</span>
        </div>
        <div class="body">
          <p v-if="todayDiary" class="sum-ex">{{ excerpt }}</p>
          <p v-else class="empty">今天还没有写 · 点这里摊开信纸</p>
        </div>
      </div>

      <div class="corner">
        <div class="sticky">
          <div class="s-head">灵感</div>
          <div class="notes">
            <p v-if="!todayFlashes.length" class="note-empty">今天还没有灵感，想到了就贴一张</p>
            <div v-for="f in todayFlashes" :key="f.id" class="note">
              {{ f.content }}
              <button class="rm" title="删除" @click.stop="removeFlash(f.id)">×</button>
              <span class="t">{{ timeOf(f.created_at) }}</span>
            </div>
          </div>
          <div class="add">
            <input v-model="flashInput" placeholder="想到了就贴" @keydown.enter="addFlash">
            <button class="btn-note" @click="addFlash">贴一张</button>
          </div>
        </div>
      </div>
    </div>

    <div class="stats">
      <div class="stat"><div class="k">总篇数</div><div class="v">{{ stats.total }}</div></div>
      <div class="stat"><div class="k">总字数</div><div class="v">{{ stats.words.toLocaleString() }}</div></div>
      <div class="stat"><div class="k">今年篇数</div><div class="v">{{ stats.year }}</div></div>
      <div class="stat"><div class="k">连续记录</div><div class="v">{{ streak }} 天</div></div>
    </div>

    <div class="charts">
      <div class="chart-card wide">
        <h3>写作热力图 · 近 6 个月</h3>
        <div class="hm">
          <i v-for="(c, i) in heatCells" :key="i" :class="c.cls" :title="c.title"></i>
        </div>
        <div class="hm-legend">少 <i class="c0"></i><i class="c1"></i><i class="c2"></i><i class="c3"></i><i class="c4"></i> 多</div>
      </div>
      <div class="chart-card">
        <h3>每月字数 &amp; 闪念条数</h3>
        <div class="bars">
          <div v-for="m in monthBars" :key="m.label" class="bar-row">
            <div class="lbl"><span>{{ m.label }}</span><span>{{ m.words.toLocaleString() }} 字 · {{ m.count }} 条闪念</span></div>
            <div class="track"><i class="diary" :style="{ width: m.wordsPct + '%' }"></i><i class="flash" :style="{ width: m.flashPct + '%' }"></i></div>
          </div>
        </div>
      </div>
      <div class="chart-card">
        <h3>常用标签</h3>
        <div class="tags">
          <div v-for="t in tagTop" :key="t.name" class="tag-row">
            <span class="name">{{ t.name }}</span>
            <div class="track"><i :style="{ width: t.pct + '%' }"></i></div>
            <span class="cnt">{{ t.count }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 弹窗 -->
    <DiaryEditorModal
      v-if="showEdit"
      :diary="todayDiary"
      :today="today"
      :saving="saving"
      @save="saveEdit"
      @delete="deleteDiary"
      @close="closeEdit"
    />
    <HistoryModal v-if="showHistory" @close="showHistory = false" @open-detail="openDetail" />
    <DetailModal v-if="showDetail && detailItem" :item="detailItem" @close="closeDetail" @delete="deleteDetail" />
  </div>
</template>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.topbar h2 {
  font-family: "Songti SC", "STSong", SimSun, serif;
  font-size: 26px;
  font-weight: 700;
  margin: 0;
  margin-right: auto;
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
.streak {
  background: var(--teal-soft);
  color: var(--teal);
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 13px;
}
.streak b {
  font-size: 15px;
}
.otd-wrap {
  position: relative;
}
.otd-pop {
  position: absolute;
  right: 0;
  top: 40px;
  width: 320px;
  z-index: 20;
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(43, 38, 34, 0.14);
  padding: 14px 16px;
}
.otd-pop .otd-date {
  font-size: 12px;
  color: var(--amber);
  font-weight: 600;
  margin-bottom: 6px;
}
.otd-pop h4 {
  font-family: var(--kai);
  font-size: 15px;
  margin-bottom: 4px;
}
.otd-pop p {
  font-size: 13px;
  color: var(--sub);
}
.error {
  color: var(--red);
  background: var(--red-soft);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 13px;
  margin-bottom: 12px;
}
.loading {
  color: var(--sub);
  font-size: 13px;
  margin-bottom: 12px;
}

/* ---------- 信纸 ---------- */
.paper {
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(43, 38, 34, 0.05);
}
.letter {
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: box-shadow 0.15s;
  background: #fdfbf7;
  font-family: var(--kai);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(43, 38, 34, 0.05), inset 0 0 60px rgba(183, 121, 31, 0.025);
}
.clickable {
  cursor: pointer;
}
.clickable:hover {
  box-shadow: 0 6px 18px rgba(43, 38, 34, 0.08);
}
.head {
  position: relative;
  padding: 16px 24px 12px;
}
.head::before {
  content: "";
  position: absolute;
  left: 24px;
  right: 24px;
  bottom: 0;
  height: 1px;
  background: #e8e2d4;
}
.head::after {
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
.page-head {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 16px 24px 10px;
}
.page-head::before,
.page-head::after {
  display: none;
}
.page-title {
  flex: 1;
  min-width: 0;
  font-size: 18px;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-bottom: 6px;
  border-bottom: 1px dashed var(--hairline);
}
.head .date {
  font-size: 14px;
  color: var(--sub);
  flex-shrink: 0;
  letter-spacing: 0.03em;
  padding-bottom: 2px;
}
.page-head .date {
  margin-right: 232px;
}
.page-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding: 10px 24px 12px;
}
.body {
  padding: 6px 24px 18px;
  flex: 1;
  display: flex;
  flex-direction: column;
  background: repeating-linear-gradient(to bottom, transparent 0 29px, #ece7da 29px 30px);
  line-height: 30px;
  font-size: 16px;
}
.sum-ex {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.empty {
  color: var(--sub);
  font-size: 15px;
}

/* ---------- 便利贴 ---------- */
.hero {
  position: relative;
  max-width: 820px;
}
.hero .letter {
  min-height: 320px;
}
.hero .letter .body {
  padding-right: 250px;
}
.corner {
  position: absolute;
  top: -12px;
  right: -14px;
  width: 230px;
  z-index: 5;
}
.sticky {
  background: var(--amber-soft);
  border: 1px solid var(--amber-line);
  border-radius: 5px;
  box-shadow: 2px 4px 10px rgba(43, 38, 34, 0.15);
  transform: rotate(3.5deg);
  position: relative;
}
.sticky::before {
  content: "";
  position: absolute;
  top: -9px;
  left: 50%;
  transform: translateX(-50%) rotate(1deg);
  width: 70px;
  height: 16px;
  background: rgba(255, 255, 255, 0.45);
  border: 1px solid var(--amber-line);
  border-bottom: none;
  border-radius: 3px 3px 0 0;
}
.s-head {
  font-family: "Songti SC", "STSong", SimSun, serif;
  font-size: 15px;
  font-weight: 700;
  color: var(--amber);
  padding: 14px 16px 4px;
}
.notes {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px 16px 12px;
  max-height: 190px;
  overflow: auto;
}
.note {
  position: relative;
  background: rgba(255, 255, 255, 0.55);
  border: 1px dashed var(--amber-line);
  border-radius: 6px;
  padding: 7px 24px 7px 10px;
  font-size: 13px;
}
.note .rm {
  position: absolute;
  top: 4px;
  right: 6px;
  border: none;
  background: none;
  color: var(--amber);
  font-size: 14px;
  cursor: pointer;
  padding: 0 2px;
}
.note .t {
  display: block;
  font-size: 11px;
  color: var(--amber);
  margin-top: 2px;
}
.note-empty {
  font-size: 12px;
  color: var(--amber);
  opacity: 0.8;
}
.add {
  display: flex;
  gap: 6px;
  padding: 0 16px 16px;
}
.add input {
  flex: 1;
  min-width: 0;
  border: 1px solid var(--amber-line);
  border-radius: 6px;
  background: #fff;
  padding: 7px 10px;
  font-size: 13px;
  outline: none;
}
.btn-note {
  border: 1px solid var(--amber);
  background: var(--amber);
  color: #fff;
  border-radius: 6px;
  padding: 7px 10px;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
}

/* ---------- 统计与图表 ---------- */
.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 24px 0 16px;
  max-width: 820px;
}
.stat {
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  padding: 14px 16px;
}
.stat .k {
  font-size: 12px;
  color: var(--sub);
}
.stat .v {
  font-family: "Songti SC", "STSong", SimSun, serif;
  font-size: 24px;
  font-weight: 700;
  color: var(--teal);
  line-height: 1.3;
}
.charts {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 14px;
  margin-bottom: 10px;
  max-width: 820px;
}
.chart-card {
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  padding: 16px 18px;
}
.chart-card.wide {
  grid-column: span 2;
}
.chart-card h3 {
  font-family: "Songti SC", "STSong", SimSun, serif;
  font-size: 15px;
  font-weight: 700;
  margin: 0 0 12px;
}
.hm {
  display: grid;
  grid-template-rows: repeat(7, 13px);
  grid-auto-flow: column;
  grid-auto-columns: 13px;
  gap: 3px;
  overflow-x: auto;
}
.hm i {
  width: 13px;
  height: 13px;
  border-radius: 3px;
  background: var(--paper-soft);
  border: 1px solid #efe9dd;
}
.hm i.c1 {
  background: #d8eae7;
  border-color: #d8eae7;
}
.hm i.c2 {
  background: #9fcdc6;
  border-color: #9fcdc6;
}
.hm i.c3 {
  background: #58a99f;
  border-color: #58a99f;
}
.hm i.c4 {
  background: var(--teal);
  border-color: var(--teal);
}
.hm-legend {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 10px;
  font-size: 11px;
  color: var(--sub);
}
.hm-legend i {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  background: var(--paper-soft);
  border: 1px solid #efe9dd;
}
.hm-legend i.c1 {
  background: #d8eae7;
  border-color: #d8eae7;
}
.hm-legend i.c2 {
  background: #9fcdc6;
  border-color: #9fcdc6;
}
.hm-legend i.c3 {
  background: #58a99f;
  border-color: #58a99f;
}
.hm-legend i.c4 {
  background: var(--teal);
  border-color: var(--teal);
}
.bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.bar-row .lbl {
  font-size: 12px;
  color: var(--sub);
  margin-bottom: 3px;
  display: flex;
  justify-content: space-between;
}
.bar-row .track {
  display: flex;
  gap: 3px;
  height: 12px;
}
.bar-row .track i {
  display: block;
  height: 100%;
  border-radius: 3px;
}
.bar-row .track i.diary {
  background: var(--teal);
}
.bar-row .track i.flash {
  background: var(--amber);
}
.tags {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.tag-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.tag-row .name {
  width: 48px;
  flex-shrink: 0;
  color: var(--sub);
}
.tag-row .track {
  flex: 1;
  height: 10px;
  background: var(--paper-soft);
  border-radius: 5px;
  overflow: hidden;
}
.tag-row .track i {
  display: block;
  height: 100%;
  background: var(--teal);
  border-radius: 5px;
}
.tag-row .cnt {
  width: 26px;
  text-align: right;
  font-size: 12px;
  color: var(--sub);
}

/* ---------- 标签 ---------- */
.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: var(--teal-soft);
  color: var(--teal);
  border: 1px solid var(--teal);
  border-radius: 999px;
  padding: 2px 9px;
  font-size: 13px;
}
.tag-chip button {
  background: none;
  border: none;
  color: var(--teal);
  font-size: 12px;
  padding: 0 0 0 2px;
  cursor: pointer;
}

@media (max-width: 820px) {
  .hero .letter .body {
    padding-right: 24px;
  }
  .corner {
    position: static;
    width: 100%;
    margin-top: -8px;
  }
  .stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts {
    grid-template-columns: 1fr;
  }
  .chart-card.wide {
    grid-column: span 1;
  }
}
</style>
