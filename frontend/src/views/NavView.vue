<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from '../api'
import { useNavStore } from '../stores/nav'

const navStore = useNavStore()
const categories = computed(() => navStore.categories)
const keyword = ref('')
const loading = ref(false)
const error = computed(() => navStore.error)
const iconFailed = ref(new Set())

const modal = reactive({ visible: false, mode: 'add', tab: 'link', editing: null })
const categoryForm = reactive({ name: '' })
const linkForm = reactive({ title: '', url: '', description: '', category_id: null, is_pinned: false })
const formError = ref('')

const ICON_EDIT =
  '<svg viewBox="0 0 1024 1024" fill="currentColor" aria-hidden="true"><path d="M526.41 117.029v58.514a7.314 7.314 0 0 1-7.315 7.314H219.429a36.571 36.571 0 0 0-35.987 29.989l-0.585 6.583V804.57a36.571 36.571 0 0 0 29.989 35.987l6.583 0.585H804.57a36.571 36.571 0 0 0 35.987-29.989l0.585-6.583v-317.44a7.314 7.314 0 0 1 7.314-7.314h58.514a7.314 7.314 0 0 1 7.315 7.314v317.44a109.714 109.714 0 0 1-99.182 109.203l-10.533 0.512H219.43a109.714 109.714 0 0 1-109.203-99.182l-0.512-10.533V219.43a109.714 109.714 0 0 1 99.182-109.203l10.533-0.512h299.666a7.314 7.314 0 0 1 7.314 7.315z m307.345 31.817l41.4 41.399a7.314 7.314 0 0 1 0 10.313L419.985 655.726a7.314 7.314 0 0 1-10.313 0l-41.399-41.4a7.314 7.314 0 0 1 0-10.312l455.168-455.168a7.314 7.314 0 0 1 10.313 0z"/></svg>'
const ICON_ADD =
  '<svg viewBox="0 0 1024 1024" fill="currentColor" aria-hidden="true"><path d="M512 1023.914667c-281.315556 0-509.269333-229.205333-509.269333-511.943111C2.730667 229.176889 230.684444 0.028444 512 0.028444c281.230222 0 509.240889 229.148444 509.240889 511.943112 0 282.794667-227.925333 511.943111-509.240889 511.943111z m0-955.704889c-243.768889 0-441.372444 198.656-441.372444 443.704889 0 244.963556 197.603556 443.676444 441.372444 443.676444 243.740444 0 441.287111-198.627556 441.344-443.676444 0-245.048889-197.603556-443.704889-441.344-443.704889z m234.382222 473.6h-199.822222l-0.881778 228.721778c0 8.476444 1.820444 44.8-37.432889 44.8-37.262222 0-33.536-23.978667-33.536-42.069334l0.085334-231.395555H255.260444c-14.336 0-31.374222 0.085333-31.374222-43.747556 0-32.568889 39.850667-28.871111 39.850667-28.871111h211.057778V248.547556c0-14.449778 11.121778-27.306667 35.84-25.856 24.718222 1.422222 35.84 11.463111 35.84 25.856v220.700444h199.850666s45.539556-5.944889 45.084445 34.588444c-0.483556 40.561778-35.868444 37.973333-45.027556 37.973334z"/></svg>'

async function loadData() {
  loading.value = true
  await navStore.refresh()
  loading.value = false
}

const filteredCategories = computed(() => {
  const kw = keyword.value.trim().toLowerCase()
  if (!kw) return categories.value
  return categories.value
    .map((cat) => ({
      ...cat,
      links: cat.links.filter(
        (link) =>
          link.title.toLowerCase().includes(kw) ||
          link.url.toLowerCase().includes(kw) ||
          (link.description || '').toLowerCase().includes(kw) ||
          cat.name.toLowerCase().includes(kw)
      )
    }))
    .filter((cat) => cat.links.length > 0)
})

const pinnedLinks = computed(() =>
  filteredCategories.value.flatMap((cat) => cat.links).filter((link) => link.is_pinned)
)

function esc(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[c]))
}

function hl(text) {
  const kw = keyword.value.trim()
  const s = esc(text)
  if (!kw) return s
  const idx = s.toLowerCase().indexOf(kw.toLowerCase())
  if (idx === -1) return s
  return s.slice(0, idx) + '<mark class="hl">' + s.slice(idx, idx + kw.length) + '</mark>' + s.slice(idx + kw.length)
}

function domainOf(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

function faviconUrl(url) {
  return '/api/nav/favicons?domain=' + encodeURIComponent(domainOf(url))
}

function handleIconError(id) {
  iconFailed.value.add(id)
}

function initials(title) {
  return (title || '').trim().slice(0, 1).toUpperCase() || '?'
}

function colorFor(seed) {
  const palette = [
    ['#e7f1ec', '#2e6b4f'],
    ['#e7f1ef', '#2d6a5b'],
    ['#fdf3e3', '#9a641a'],
    ['#f1ecf9', '#6d4da8'],
    ['#e8effa', '#2f5aa8'],
    ['#f9ebe5', '#a8442e'],
    ['#e8f4f3', '#0a6a63']
  ]
  let h = 0
  for (const c of String(seed)) h = (h * 31 + c.charCodeAt(0)) >>> 0
  return palette[h % palette.length]
}

function iconStyle(link) {
  const [bg, fg] = colorFor(link.title)
  return { '--bg': bg, '--fg': fg }
}

function resetForms() {
  categoryForm.name = ''
  linkForm.title = ''
  linkForm.url = ''
  linkForm.description = ''
  linkForm.category_id = categories.value[0]?.id || null
  linkForm.is_pinned = false
  formError.value = ''
}

function openAdd() {
  resetForms()
  modal.mode = 'add'
  modal.tab = 'link'
  modal.editing = null
  modal.visible = true
}

function openEdit(link) {
  resetForms()
  modal.mode = 'edit'
  modal.tab = 'link'
  modal.editing = link
  linkForm.title = link.title
  linkForm.url = link.url
  linkForm.description = link.description || ''
  linkForm.category_id = link.category_id
  linkForm.is_pinned = link.is_pinned
  modal.visible = true
}

function closeModal() {
  modal.visible = false
}

function save() {
  if (modal.tab === 'category') saveCategory()
  else saveLink()
}

async function saveCategory() {
  const name = categoryForm.name.trim()
  if (!name) {
    formError.value = '请输入分类名称'
    return
  }
  try {
    await api.post('/nav/categories', { name, sort_order: categories.value.length })
    closeModal()
    await loadData()
  } catch (e) {
    formError.value = e.response?.data?.detail || '保存分类失败'
  }
}

async function saveLink() {
  if (!linkForm.title.trim() || !linkForm.url.trim() || !linkForm.category_id) {
    formError.value = '请填写标题、URL 和分类'
    return
  }
  const payload = {
    title: linkForm.title.trim(),
    url: linkForm.url.trim(),
    description: linkForm.description.trim() || null,
    category_id: linkForm.category_id,
    is_pinned: linkForm.is_pinned
  }
  try {
    if (modal.editing) {
      await api.put(`/nav/links/${modal.editing.id}`, payload)
    } else {
      await api.post('/nav/links', payload)
    }
    closeModal()
    await loadData()
  } catch (e) {
    formError.value = e.response?.data?.detail || '保存链接失败'
  }
}

async function deleteEditingLink() {
  if (!modal.editing) return
  if (!confirm(`确定删除链接「${modal.editing.title}」？`)) return
  try {
    await api.delete(`/nav/links/${modal.editing.id}`)
    closeModal()
    await loadData()
  } catch (e) {
    formError.value = e.response?.data?.detail || '删除链接失败'
  }
}

onMounted(() => {
  if (!navStore.loaded) loadData()
})
</script>

<template>
  <div class="page vc">
    <header class="vc-bar">
      <div class="vc-bar-main">
        <h1>导航</h1>
        <input v-model="keyword" class="search" type="text" placeholder="搜索标题、分类或网址…" />
      </div>
      <div class="vc-bar-actions">
        <button class="icon-btn-primary" title="新增" @click="openAdd">
          <span v-html="ICON_ADD"></span>
          <span>新增</span>
        </button>
      </div>
    </header>

    <p v-if="error" class="nav-note nav-error">{{ error }}</p>
    <p v-if="loading" class="nav-note">加载中…</p>
    <p v-else-if="!filteredCategories.length" class="nav-note">暂无导航内容，先点右上角「新增」创建一个吧。</p>

    <section v-if="pinnedLinks.length" class="vc-section">
      <h2 class="sec-title">常用<span class="count">{{ pinnedLinks.length }}</span></h2>
      <div class="vc-strip">
        <div v-for="link in pinnedLinks" :key="link.id" class="vc-chip">
          <a class="vc-chip-main" :href="link.url" target="_blank" rel="noopener">
            <span class="tile-icon" :style="iconStyle(link)">
              <img
                v-if="!iconFailed.has(link.id)"
                :src="faviconUrl(link.url)"
                alt=""
                loading="lazy"
                @error="handleIconError(link.id)"
              />
              <span v-else class="fallback">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
                  <circle cx="12" cy="12" r="9" />
                  <path d="M3 12h18M12 3c3.2 3.4 3.2 14.2 0 18M12 3c-3.2 3.4-3.2 14.2 0 18" />
                </svg>
              </span>
            </span>
            <span class="vc-chip-title" v-html="hl(link.title)"></span>
          </a>
          <button class="tile-action-btn" title="编辑" @click="openEdit(link)">
            <span v-html="ICON_EDIT"></span>
          </button>
        </div>
      </div>
    </section>

    <section v-for="category in filteredCategories" :key="category.id" class="vc-band">
      <div class="vc-band-head">
        <h2>{{ category.name }}</h2>
        <span class="count">{{ category.links.length }}</span>
      </div>
      <div v-if="category.links.length" class="vc-grid">
        <div v-for="link in category.links" :key="link.id" class="vc-tile">
          <span class="tile-icon" :style="iconStyle(link)">
            <img
              v-if="!iconFailed.has(link.id)"
              :src="faviconUrl(link.url)"
              alt=""
              loading="lazy"
              @error="handleIconError(link.id)"
            />
            <span v-else class="mono">{{ initials(link.title) }}</span>
          </span>
          <a class="vc-tile-main" :href="link.url" target="_blank" rel="noopener">
            <span class="vc-tile-title" v-html="hl(link.title)"></span>
            <br />
            <span class="vc-tile-domain">{{ domainOf(link.url) }}</span>
          </a>
          <button class="tile-action-btn" title="编辑" @click="openEdit(link)">
            <span v-html="ICON_EDIT"></span>
          </button>
        </div>
      </div>
      <p v-else class="nav-note">该分类下暂无链接</p>
    </section>

    <div v-if="modal.visible" class="modal-mask" @click.self="closeModal">
      <div class="modal">
        <div class="modal-head">
          <h3>{{ modal.mode === 'add' ? '新增' : '编辑链接' }}</h3>
        </div>
        <div v-if="modal.mode === 'add'" class="modal-tabs">
          <button
            type="button"
            class="modal-tab"
            :class="{ active: modal.tab === 'category' }"
            @click="modal.tab = 'category'"
          >
            新建分类
          </button>
          <button
            type="button"
            class="modal-tab"
            :class="{ active: modal.tab === 'link' }"
            @click="modal.tab = 'link'"
          >
            新建链接
          </button>
        </div>

        <form @submit.prevent="save">
          <template v-if="modal.tab === 'category'">
            <div class="field">
              <label>分类名称</label>
              <input v-model="categoryForm.name" type="text" placeholder="例如：图片生成" />
            </div>
          </template>
          <template v-else>
            <div class="field">
              <label>标题</label>
              <input v-model="linkForm.title" type="text" placeholder="链接名称" />
            </div>
            <div class="field">
              <label>URL</label>
              <input v-model="linkForm.url" type="url" placeholder="https://" />
            </div>
            <div class="field">
              <label>描述（可选）</label>
              <input v-model="linkForm.description" type="text" />
            </div>
            <div class="field">
              <label>分类</label>
              <select v-model="linkForm.category_id">
                <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
              </select>
            </div>
            <label class="check-row">
              <input v-model="linkForm.is_pinned" type="checkbox" /> 置顶
            </label>
          </template>

          <p v-if="formError" class="nav-note nav-error">{{ formError }}</p>

          <div class="modal-foot">
            <button v-if="modal.mode === 'edit'" type="button" class="btn btn-danger" @click="deleteEditingLink">
              删除
            </button>
            <button type="button" class="btn" @click="closeModal">取消</button>
            <button type="submit" class="btn btn-primary">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  --paper: #f7f5f1;
  --paper-soft: #f4f1ea;
  --card: #fffefc;
  --hairline: #e9e3d9;
  --ink: #2b2622;
  --sub: #7c7468;
  --teal: #0e7c74;
  --teal-dark: #0a6a63;
  --teal-soft: #e7f1ef;
  --amber: #b7791f;
  --amber-soft: #faf1dd;
  --red: #c4533a;
  --red-soft: #f9ebe5;
  --serif: "Songti SC", "STSong", SimSun, serif;
  --sans: "PingFang SC", "Microsoft YaHei", "Segoe UI", system-ui, sans-serif;
  max-width: 1120px;
  margin: 0 auto;
  padding: 40px 28px 90px;
}

h1,
h2,
h3 {
  font-family: var(--serif);
  font-weight: 700;
  margin: 0;
}
a {
  color: inherit;
  text-decoration: none;
}
button {
  font: inherit;
  border: 0;
  background: none;
  cursor: pointer;
  color: inherit;
}

.search {
  width: 100%;
  border: 1px solid var(--hairline);
  border-radius: 10px;
  background: var(--card);
  padding: 10px 14px;
  font-size: 14px;
  color: var(--ink);
}
.search::placeholder {
  color: var(--sub);
}
.search:focus {
  border-color: var(--teal);
  outline: none;
  box-shadow: 0 0 0 3px var(--teal-soft);
}
.sec-title {
  font-size: 17px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.count {
  font-family: var(--sans);
  font-size: 12px;
  font-weight: 500;
  color: var(--sub);
  background: var(--paper-soft);
  border-radius: 999px;
  padding: 1px 9px;
}
.nav-note {
  color: var(--sub);
  font-size: 14px;
  margin: 0 0 16px;
}
.nav-error {
  color: var(--red);
  background: var(--red-soft);
  border-radius: 8px;
  padding: 8px 12px;
}

.tile-icon {
  position: relative;
  width: 46px;
  height: 46px;
  border-radius: 12px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  background: var(--bg, var(--teal-soft));
  color: var(--fg, var(--teal-dark));
  overflow: hidden;
  border: 1px solid var(--hairline);
}
.tile-icon img {
  width: 24px;
  height: 24px;
  object-fit: contain;
}
.tile-icon .mono {
  font-family: var(--serif);
  font-size: 19px;
  font-weight: 700;
  line-height: 1;
}
.tile-icon .fallback {
  display: grid;
  place-items: center;
}

.vc-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  position: sticky;
  top: 0;
  z-index: 20;
  background: rgba(247, 245, 241, 0.92);
  backdrop-filter: blur(6px);
  padding: 16px 0;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--hairline);
}
.vc-bar h1 {
  font-size: 22px;
  letter-spacing: 2px;
}
.vc-bar-main {
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
}
.vc-bar .search {
  width: 320px;
}
.vc-bar-actions {
  display: flex;
  gap: 10px;
}
.icon-btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border-radius: 999px;
  background: var(--teal);
  border: 1px solid var(--teal);
  padding: 8px 16px 8px 12px;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.12s ease;
}
.icon-btn-primary:hover {
  background: var(--teal-dark);
}
.icon-btn-primary :deep(svg) {
  width: 18px;
  height: 18px;
  display: block;
}

.vc-section {
  margin-bottom: 26px;
}
.vc-strip {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding: 12px 2px 16px;
  margin-top: 8px;
}
.vc-chip {
  position: relative;
  flex-shrink: 0;
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 999px;
  padding: 8px 14px 8px 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: border-color 0.14s ease, background 0.14s ease;
}
.vc-chip:hover {
  border-color: var(--teal);
  background: var(--teal-soft);
}
.vc-chip-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}
.vc-chip .tile-icon {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}
.vc-chip .tile-icon img {
  width: 14px;
  height: 14px;
}
.vc-chip .mono {
  font-size: 11px;
}
.vc-chip-title {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.vc-band {
  margin-bottom: 8px;
  padding-top: 18px;
  border-top: 1px dashed var(--hairline);
}
.vc-band-head {
  display: flex;
  align-items: baseline;
  justify-content: flex-start;
  gap: 10px;
  margin-bottom: 12px;
}
.vc-band-head h2 {
  font-size: 16px;
}
.vc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}
.vc-tile {
  position: relative;
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 11px;
  padding: 11px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: border-color 0.12s ease, background 0.12s ease;
}
.vc-tile:hover {
  border-color: var(--teal);
  background: var(--teal-soft);
}
.vc-tile .tile-icon {
  width: 28px;
  height: 28px;
  border-radius: 8px;
}
.vc-tile .tile-icon img {
  width: 15px;
  height: 15px;
}
.vc-tile .mono {
  font-size: 12px;
}
.vc-tile-main {
  min-width: 0;
  flex: 1;
}
.vc-tile-title {
  font-size: 13px;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.vc-tile-domain {
  font-size: 11px;
  color: var(--sub);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tile-action-btn {
  position: absolute;
  top: -7px;
  right: -5px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  line-height: 0;
  background: var(--card);
  border: 1px solid var(--hairline);
  display: grid;
  place-items: center;
  color: var(--sub);
  opacity: 0;
  transition: opacity 0.12s ease, color 0.12s ease, border-color 0.12s ease;
}
.tile-action-btn :deep(svg) {
  width: 12px;
  height: 12px;
  display: block;
}
.tile-action-btn:hover {
  color: var(--teal);
  border-color: var(--teal);
}
.vc-tile:hover .tile-action-btn,
.vc-tile:focus-within .tile-action-btn,
.vc-chip:hover .tile-action-btn,
.vc-chip:focus-within .tile-action-btn {
  opacity: 1;
}

.modal-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
  background: rgba(43, 38, 34, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal {
  width: 100%;
  max-width: 420px;
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 16px;
  padding: 22px;
  box-shadow: 0 16px 40px rgba(43, 38, 34, 0.18);
}
.modal-head h3 {
  font-size: 18px;
  margin-bottom: 14px;
}
.modal-tabs {
  display: flex;
  gap: 4px;
  background: var(--paper-soft);
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 16px;
}
.modal-tab {
  flex: 1;
  padding: 7px 0;
  border-radius: 8px;
  font-size: 14px;
  color: var(--sub);
  text-align: center;
}
.modal-tab.active {
  background: var(--card);
  color: var(--teal-dark);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(43, 38, 34, 0.08);
}
.field {
  margin-bottom: 12px;
}
.field label {
  display: block;
  font-size: 13px;
  color: var(--sub);
  margin-bottom: 5px;
}
.field input,
.field select {
  width: 100%;
  border: 1px solid var(--hairline);
  border-radius: 10px;
  background: var(--card);
  padding: 9px 12px;
  font-size: 14px;
  color: var(--ink);
}
.field input:focus,
.field select:focus {
  border-color: var(--teal);
  outline: none;
  box-shadow: 0 0 0 3px var(--teal-soft);
}
.check-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--sub);
  margin-bottom: 16px;
}
.modal-foot {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.btn {
  border: 1px solid var(--hairline);
  border-radius: 10px;
  background: var(--card);
  padding: 8px 16px;
  font-size: 14px;
  color: var(--ink);
}
.btn:hover {
  border-color: var(--teal);
  color: var(--teal);
}
.btn-primary {
  background: var(--teal);
  border-color: var(--teal);
  color: #fff;
}
.btn-primary:hover {
  background: var(--teal-dark);
  color: #fff;
}
.btn-danger {
  border-color: var(--red);
  color: var(--red);
  margin-right: auto;
}
.btn-danger:hover {
  background: var(--red-soft);
  color: var(--red);
}

.vc-tile-title :deep(mark.hl),
.vc-chip-title :deep(mark.hl) {
  background: var(--amber-soft);
  color: var(--amber);
  border-radius: 2px;
  padding: 0 1px;
}

@media (max-width: 880px) {
  .vc-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .vc-bar-main {
    flex-direction: column;
    align-items: stretch;
  }
  .vc-bar .search {
    width: 100%;
  }
  .vc-bar-actions {
    justify-content: flex-end;
  }
}
@media (prefers-reduced-motion: reduce) {
  * {
    transition: none !important;
    animation: none !important;
  }
}
</style>
