<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from '../api'

const categories = ref([])
const keyword = ref('')
const loading = ref(false)
const error = ref('')
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
  error.value = ''
  try {
    const { data } = await api.get('/nav/categories')
    categories.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || '加载导航数据失败'
  } finally {
    loading.value = false
  }
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

onMounted(loadData)
</script>

<template>
  <div>
    <header class="sticky top-0 z-20 -mx-8 mb-6 border-b border-hairline bg-paper/90 px-8 py-4 backdrop-blur">
      <div class="flex items-center justify-between gap-4">
        <div class="flex flex-1 items-center gap-4">
          <h2 class="font-serif text-2xl font-bold text-ink">导航</h2>
          <input
            v-model="keyword"
            type="text"
            placeholder="搜索标题、分类或网址…"
            class="w-80 max-w-full rounded border border-hairline bg-card px-3 py-2 text-sm focus:border-teal focus:outline-none"
          />
        </div>
        <button class="btn-add" title="新增" @click="openAdd">
          <span v-html="ICON_ADD"></span>
          <span>新增</span>
        </button>
      </div>
    </header>

    <p v-if="error" class="mb-4 rounded bg-red-soft px-3 py-2 text-sm text-red">{{ error }}</p>
    <p v-if="loading" class="text-sm text-sub">加载中…</p>
    <p v-else-if="!filteredCategories.length" class="text-sm text-sub">暂无导航内容，先点右上角「新增」创建一个吧。</p>

    <section v-if="pinnedLinks.length" class="mb-8">
      <div class="mb-3 flex items-center gap-2">
        <h3 class="font-serif text-lg font-bold text-ink">常用</h3>
        <span class="count-badge">{{ pinnedLinks.length }}</span>
      </div>
      <div class="flex gap-2.5 overflow-x-auto pb-2">
        <div v-for="link in pinnedLinks" :key="link.id" class="chip group relative shrink-0">
          <a :href="link.url" target="_blank" rel="noopener" class="chip-main">
            <span class="icon-wrap h-6 w-6 rounded-full" :style="iconStyle(link)">
              <img
                v-if="!iconFailed.has(link.id)"
                :src="faviconUrl(link.url)"
                alt=""
                class="h-3.5 w-3.5 object-contain"
                @error="handleIconError(link.id)"
              />
              <svg
                v-else
                viewBox="0 0 24 24"
                class="h-3.5 w-3.5"
                fill="none"
                stroke="currentColor"
                stroke-width="1.8"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="9" />
                <path d="M3 12h18M12 3c3.2 3.4 3.2 14.2 0 18M12 3c-3.2 3.4-3.2 14.2 0 18" />
              </svg>
            </span>
            <span class="chip-title">{{ link.title }}</span>
          </a>
          <button class="edit-badge" title="编辑" @click="openEdit(link)">
            <span v-html="ICON_EDIT"></span>
          </button>
        </div>
      </div>
    </section>

    <section
      v-for="category in filteredCategories"
      :key="category.id"
      class="mb-7 border-t border-dashed border-hairline pt-4"
    >
      <div class="mb-3 flex items-baseline gap-2.5">
        <h3 class="font-serif text-lg font-bold text-ink">{{ category.name }}</h3>
        <span class="count-badge">{{ category.links.length }}</span>
      </div>

      <ul v-if="category.links.length" class="grid grid-cols-[repeat(auto-fill,minmax(150px,1fr))] gap-2.5">
        <li
          v-for="link in category.links"
          :key="link.id"
          class="group relative flex items-center gap-2.5 rounded-lg border border-hairline bg-card px-3 py-2.5 transition hover:border-teal hover:bg-teal-soft"
        >
          <span class="icon-wrap h-7 w-7 rounded-lg" :style="iconStyle(link)">
            <img
              v-if="!iconFailed.has(link.id)"
              :src="faviconUrl(link.url)"
              alt=""
              class="h-4 w-4 object-contain"
              @error="handleIconError(link.id)"
            />
            <span v-else class="font-serif text-sm font-bold">{{ initials(link.title) }}</span>
          </span>
          <a :href="link.url" target="_blank" rel="noopener" class="min-w-0 flex-1">
            <span class="block truncate text-[13px] font-semibold">{{ link.title }}</span>
            <span class="block truncate text-[11px] text-sub">{{ domainOf(link.url) }}</span>
          </a>
          <button class="edit-badge" title="编辑" @click="openEdit(link)">
            <span v-html="ICON_EDIT"></span>
          </button>
        </li>
      </ul>
      <p v-else class="py-2 text-sm text-sub">该分类下暂无链接</p>
    </section>

    <div
      v-if="modal.visible"
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-5"
      @click.self="closeModal"
    >
      <div class="w-full max-w-md rounded-2xl border border-hairline bg-card p-6 shadow-2xl">
        <h3 class="mb-4 text-lg font-semibold">{{ modal.mode === 'add' ? '新增' : '编辑链接' }}</h3>

        <div v-if="modal.mode === 'add'" class="mb-4 flex gap-1 rounded-xl bg-paper-soft p-1">
          <button
            type="button"
            class="flex-1 rounded-lg py-1.5 text-sm text-sub"
            :class="modal.tab === 'category' ? 'tab-active' : ''"
            @click="modal.tab = 'category'"
          >
            新建分类
          </button>
          <button
            type="button"
            class="flex-1 rounded-lg py-1.5 text-sm text-sub"
            :class="modal.tab === 'link' ? 'tab-active' : ''"
            @click="modal.tab = 'link'"
          >
            新建链接
          </button>
        </div>

        <form @submit.prevent="save">
          <template v-if="modal.tab === 'category'">
            <label class="mb-1 block text-sm text-sub">分类名称</label>
            <input v-model="categoryForm.name" type="text" placeholder="例如：图片生成" class="input-field" />
          </template>
          <template v-else>
            <label class="mb-1 block text-sm text-sub">标题</label>
            <input v-model="linkForm.title" type="text" placeholder="链接名称" class="input-field" />
            <label class="mb-1 mt-3 block text-sm text-sub">URL</label>
            <input v-model="linkForm.url" type="url" placeholder="https://" class="input-field" />
            <label class="mb-1 mt-3 block text-sm text-sub">描述（可选）</label>
            <input v-model="linkForm.description" type="text" class="input-field" />
            <label class="mb-1 mt-3 block text-sm text-sub">分类</label>
            <select v-model="linkForm.category_id" class="input-field">
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
            <label class="mt-3 flex items-center gap-2 text-sm text-sub">
              <input v-model="linkForm.is_pinned" type="checkbox" /> 置顶
            </label>
          </template>

          <p v-if="formError" class="mt-3 rounded bg-red-soft px-3 py-2 text-sm text-red">{{ formError }}</p>

          <div class="mt-5 flex items-center justify-between gap-2">
            <button
              v-if="modal.mode === 'edit'"
              type="button"
              class="rounded border border-red/40 px-4 py-2 text-sm text-red hover:bg-red-soft"
              @click="deleteEditingLink"
            >
              删除
            </button>
            <div class="flex flex-1 justify-end gap-2">
              <button type="button" class="rounded border border-hairline px-4 py-2 text-sm" @click="closeModal">
                取消
              </button>
              <button type="submit" class="rounded bg-teal px-4 py-2 text-sm text-white hover:bg-teal-dark">
                保存
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.icon-wrap {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  overflow: hidden;
  background: var(--bg, #e7f1ef);
  color: var(--fg, #0a6a63);
  border: 1px solid var(--hairline);
}
.chip {
  border: 1px solid var(--hairline);
  border-radius: 999px;
  background: var(--card);
  transition: border-color 0.14s ease, background 0.14s ease;
}
.chip:hover {
  border-color: var(--teal);
  background: var(--teal-soft);
}
.chip-main {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px 8px 10px;
}
.chip-title {
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}
.count-badge {
  border-radius: 999px;
  background: var(--paper-soft);
  color: var(--sub);
  font-size: 12px;
  padding: 1px 9px;
}
.btn-add {
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
.btn-add:hover {
  background: var(--teal-dark);
}
.btn-add svg {
  width: 18px;
  height: 18px;
  display: block;
}
.edit-badge {
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
.edit-badge svg {
  width: 12px;
  height: 12px;
  display: block;
  transform: translateX(-1px);
}
.edit-badge:hover {
  color: var(--teal);
  border-color: var(--teal);
}
.group:hover .edit-badge,
.group:focus-within .edit-badge {
  opacity: 1;
}
.tab-active {
  background: var(--card);
  color: var(--teal-dark);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(43, 38, 34, 0.08);
}
.input-field {
  width: 100%;
  border: 1px solid var(--hairline);
  border-radius: 10px;
  background: var(--card);
  padding: 9px 12px;
  font-size: 14px;
  color: var(--ink);
}
.input-field:focus {
  border-color: var(--teal);
  outline: none;
  box-shadow: 0 0 0 3px var(--teal-soft);
}
</style>
