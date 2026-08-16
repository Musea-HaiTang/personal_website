<script setup>
import { computed, onMounted, ref } from 'vue'
import api from '../api'
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
function fmtDate(d) {
  const [y, m, dd] = d.split('-')
  return `${y}.${m}.${dd}`
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

const allTags = computed(() => [...new Set(entries.value.flatMap((e) => e.tags || []))].sort())

async function loadAll() {
  loading.value = true
  error.value = ''
  await diaryStore.refresh()
  error.value = diaryStore.error
  loading.value = false
}

/* ---------- 编辑弹窗 ---------- */
const showEdit = ref(false)
const editTitle = ref('')
const editContent = ref('')
const selectedTags = ref([])
const showTagPop = ref(false)
const newTag = ref('')
const editWords = computed(() => editContent.value.replace(/\s/g, '').length)

function openEdit() {
  editTitle.value = todayDiary.value?.title || ''
  editContent.value = todayDiary.value?.content || ''
  selectedTags.value = [...(todayDiary.value?.tags || [])]
  showTagPop.value = false
  showEdit.value = true
}
function closeEdit() {
  showEdit.value = false
}
function toggleTag(t) {
  selectedTags.value = selectedTags.value.includes(t) ? selectedTags.value.filter((x) => x !== t) : [...selectedTags.value, t]
}
function removeTag(t) {
  selectedTags.value = selectedTags.value.filter((x) => x !== t)
}
function addNewTag() {
  const v = newTag.value.trim()
  if (!v) return
  if (!selectedTags.value.includes(v)) selectedTags.value.push(v)
  newTag.value = ''
}

async function saveEdit() {
  const title = editTitle.value.trim() || '无标题'
  saving.value = true
  error.value = ''
  const payload = { date: today, title, tags: selectedTags.value, content: editContent.value }
  try {
    if (todayDiary.value) await api.put(`/diary/${todayDiary.value.id}`, payload)
    else await api.post('/diary', payload)
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
    await api.delete(`/diary/${todayDiary.value.id}`)
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
    await api.post('/flash', { content: v })
    flashInput.value = ''
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || '记录灵感失败'
  }
}

async function removeFlash(id) {
  try {
    await api.delete(`/flash/${id}`)
    await loadAll()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除灵感失败'
  }
}

/* ---------- 往日记录 ---------- */
const showHistory = ref(false)
const histTab = ref('all')
const histQuery = ref('')

const histItems = computed(() => {
  const items = []
  entries.value.forEach((e) => items.push({ id: e.id, kind: 'diary', sort: e.date + 'T00:00:00', label: fmtDate(e.date), title: e.title, tags: e.tags, excerpt: strip(e.content), full: e.content }))
  flashes.value.forEach((f) => {
    const s = String(f.created_at)
    items.push({ id: f.id, kind: 'flash', sort: s, label: s.slice(5, 10).replace('-', '/') + ' ' + s.slice(11, 16), title: f.content, full: f.content })
  })
  return items.sort((a, b) => b.sort.localeCompare(a.sort))
})

const filteredHist = computed(() => {
  const q = histQuery.value.trim().toLowerCase()
  return histItems.value.filter((it) => (histTab.value === 'all' || it.kind === histTab.value) && (!q || (it.title + ' ' + (it.excerpt || '') + ' ' + (it.tags || []).join(' ')).toLowerCase().includes(q)))
})

function plainText(s) {
  return (s || '').replace(/^#+\s*/gm, '')
}

/* ---------- 详情弹窗 ---------- */
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
    await api.delete(it.kind === 'flash' ? `/flash/${it.id}` : `/diary/${it.id}`)
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

    <!-- 编辑弹窗 -->
    <div v-if="showEdit" class="edit-overlay" @click.self="closeEdit">
      <div class="paper letter edit-modal">
        <div class="head edit-head">
          <input v-model="editTitle" class="title-input" placeholder="标题">
          <div class="date">{{ dateLabel }}</div>
        </div>
        <div class="edit-scroll" @click="showTagPop = false">
          <div class="tag-zone" @click.stop>
            <div class="tag-selected">
              <span v-for="t in selectedTags" :key="t" class="tag-chip">{{ t }}<button type="button" @click="removeTag(t)">×</button></span>
            </div>
            <button type="button" class="btn tag-open" @click="showTagPop = !showTagPop">＋ 标签</button>
            <div v-if="showTagPop" class="tag-pop">
              <h5>常用标签</h5>
              <div class="tag-pop-list">
                <button v-for="t in allTags" :key="t" type="button" class="tag-opt" :class="{ on: selectedTags.includes(t) }" @click="toggleTag(t)">{{ t }}</button>
              </div>
              <div class="tag-pop-add">
                <input v-model="newTag" placeholder="新标签" @keydown.enter="addNewTag">
                <button type="button" @click="addNewTag">添加</button>
              </div>
            </div>
          </div>
          <textarea v-model="editContent" class="edit-content" rows="14" placeholder="用 Markdown 写今天的日记…"></textarea>
        </div>
        <div class="ed-actions">
          <span class="wc">已写 {{ editWords.toLocaleString() }} 字</span>
          <button v-if="todayDiary" type="button" class="btn danger" @click="deleteDiary">删除</button>
          <button type="button" class="btn" @click="closeEdit">取消</button>
          <button type="button" class="btn btn-teal" :disabled="saving" @click="saveEdit">{{ saving ? '保存中…' : '保存' }}</button>
        </div>
      </div>
    </div>

    <!-- 往日记录弹窗 -->
    <div v-if="showHistory" class="overlay" @click.self="showHistory = false">
      <div class="modal">
        <div class="m-head">
          <h3>往日记录</h3>
          <button type="button" class="btn" @click="showHistory = false">关闭</button>
        </div>
        <div class="tabs">
          <button v-for="k in [['all', '全部'], ['diary', '日记'], ['flash', '闪念']]" :key="k[0]" type="button" class="tab" :class="{ active: histTab === k[0] }" @click="histTab = k[0]">{{ k[1] }}</button>
        </div>
        <div class="m-body">
          <input v-model="histQuery" class="search" placeholder="搜索标题 / 标签 / 内容…">
          <div class="timeline">
            <div v-for="(it, i) in filteredHist" :key="i" class="tl" :class="{ flash: it.kind === 'flash' }" @click="openDetail(it)">
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

    <!-- 详情弹窗 -->
    <div v-if="showDetail && detailItem" class="detail-overlay" @click.self="closeDetail">
      <div class="detail-card" :class="{ flash: detailItem.kind === 'flash' }">
        <div class="d-head">
          <h4 class="d-title">{{ detailItem.kind === 'flash' ? '闪念' : (detailItem.title || '无标题') }}</h4>
          <div class="d-date">{{ detailItem.label }}</div>
        </div>
        <div v-if="detailItem.tags && detailItem.tags.length" class="d-tags">
          <span v-for="t in detailItem.tags" :key="t" class="tag">{{ t }}</span>
        </div>
        <div class="d-body">{{ plainText(detailItem.full) }}</div>
        <div class="d-actions">
          <button type="button" class="btn danger" @click="deleteDetail">删除</button>
          <button type="button" class="btn" @click="closeDetail">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.diary-page {
  --hairline: #e9e3d9;
  --card: #fffefc;
  --paper-soft: #f4f1ea;
  --sub: #7c7468;
  --ink: #2b2622;
  --teal: #0e7c74;
  --teal-dark: #0a6a63;
  --teal-soft: #e7f1ef;
  --amber: #b7791f;
  --amber-soft: #faf1dd;
  --amber-line: #e8d6a8;
  --red: #c4533a;
  --red-soft: #f9ebe5;
  --kai: "KaiTi", "STKaiti", "Kaiti SC", "楷体", serif;
}

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
.btn-teal {
  background: var(--teal);
  border-color: var(--teal);
  color: #fff;
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
.btn.danger {
  color: var(--red);
  border-color: var(--red);
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
  margin-bottom: 12px;
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
.tag {
  background: var(--paper-soft);
  color: var(--sub);
  border-radius: 999px;
  padding: 2px 9px;
  font-size: 12px;
}

/* ---------- 编辑弹窗 ---------- */
.edit-overlay,
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(43, 38, 34, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 24px;
}
.edit-modal {
  width: min(680px, 100%);
  max-height: 88vh;
  box-shadow: 0 24px 70px rgba(43, 38, 34, 0.4);
  background: #fdfbf7;
  display: flex;
  flex-direction: column;
}
.edit-head {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 14px 24px 10px;
}
.edit-head::before {
  display: none;
}
.edit-head .date {
  margin-right: 34px;
}
.title-input {
  flex: 1;
  min-width: 0;
  border: none;
  border-bottom: 1px dashed var(--hairline);
  background: transparent;
  font-family: var(--kai);
  font-size: 22px;
  font-weight: 700;
  padding: 2px 2px 6px;
  outline: none;
}
.edit-scroll {
  flex: 1;
  overflow: auto;
  padding: 12px 24px 18px;
}
.tag-zone {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.tag-selected {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.tag-pop {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 30;
  width: 300px;
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(43, 38, 34, 0.16);
  padding: 14px;
}
.tag-pop h5 {
  font-size: 12px;
  color: var(--sub);
  margin: 0 0 8px;
}
.tag-pop-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.tag-opt {
  border: 1px solid var(--hairline);
  background: var(--card);
  color: var(--sub);
  border-radius: 999px;
  padding: 3px 11px;
  font-size: 13px;
  cursor: pointer;
}
.tag-opt.on {
  background: var(--teal-soft);
  border-color: var(--teal);
  color: var(--teal);
  font-weight: 600;
}
.tag-pop-add {
  display: flex;
  gap: 6px;
}
.tag-pop-add input {
  flex: 1;
  min-width: 0;
  border: 1px solid var(--hairline);
  border-radius: 6px;
  padding: 5px 9px;
  font-size: 13px;
  outline: none;
}
.tag-pop-add button {
  border: 1px solid var(--hairline);
  background: var(--card);
  border-radius: 6px;
  padding: 5px 10px;
  font-size: 13px;
  color: var(--ink);
  cursor: pointer;
}
.edit-content {
  width: 100%;
  min-height: 300px;
  border: none;
  resize: vertical;
  font-family: var(--kai);
  font-size: 16px;
  line-height: 30px;
  outline: none;
  padding: 6px 0;
  background: repeating-linear-gradient(to bottom, transparent 0 29px, #ece7da 29px 30px);
}
.ed-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  align-items: center;
  padding: 12px 22px;
  border-top: 1px solid var(--hairline);
}
.wc {
  font-size: 12px;
  color: var(--sub);
  margin-right: auto;
}

/* ---------- 往日记录弹窗 ---------- */
.overlay {
  align-items: flex-start;
  padding-top: 7vh;
}
.modal {
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 16px;
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

/* ---------- 详情弹窗 ---------- */
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
