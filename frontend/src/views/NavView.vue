<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from '../api'

const categories = ref([])
const keyword = ref('')
const loading = ref(false)
const error = ref('')
const iconFailed = ref(new Set())

const modal = reactive({ visible: false, type: null, editing: null })
const categoryForm = reactive({ name: '' })
const linkForm = reactive({ title: '', url: '', description: '', category_id: null, is_pinned: false })

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
  return 'https://www.google.com/s2/favicons?domain=' + encodeURIComponent(domainOf(url)) + '&sz=64'
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

function openCategoryModal(category = null) {
  modal.type = 'category'
  modal.editing = category
  categoryForm.name = category ? category.name : ''
  modal.visible = true
}

function openLinkModal(category = null, link = null) {
  modal.type = 'link'
  modal.editing = link
  linkForm.title = link ? link.title : ''
  linkForm.url = link ? link.url : ''
  linkForm.description = link ? link.description || '' : ''
  linkForm.category_id = link ? link.category_id : category ? category.id : categories.value[0]?.id || null
  linkForm.is_pinned = link ? link.is_pinned : false
  modal.visible = true
}

function closeModal() {
  modal.visible = false
}

async function saveCategory() {
  const name = categoryForm.name.trim()
  if (!name) return
  try {
    if (modal.editing) {
      await api.put(`/nav/categories/${modal.editing.id}`, { name })
    } else {
      await api.post('/nav/categories', { name, sort_order: categories.value.length })
    }
    closeModal()
    await loadData()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存分类失败'
  }
}

async function deleteCategory(category) {
  if (!confirm(`确定删除分类「${category.name}」及其下所有链接？`)) return
  try {
    await api.delete(`/nav/categories/${category.id}`)
    await loadData()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除分类失败'
  }
}

async function saveLink() {
  if (!linkForm.title.trim() || !linkForm.url.trim() || !linkForm.category_id) return
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
    error.value = e.response?.data?.detail || '保存链接失败'
  }
}

async function deleteLink(link) {
  if (!confirm(`确定删除链接「${link.title}」？`)) return
  try {
    await api.delete(`/nav/links/${link.id}`)
    await loadData()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除链接失败'
  }
}

async function togglePin(link) {
  try {
    await api.put(`/nav/links/${link.id}`, { is_pinned: !link.is_pinned })
    await loadData()
  } catch (e) {
    error.value = e.response?.data?.detail || '操作失败'
  }
}

async function moveLink(category, link, direction) {
  const links = category.links
  const index = links.findIndex((l) => l.id === link.id)
  const target = index + direction
  if (target < 0 || target >= links.length) return
  const other = links[target]
  try {
    await api.put(`/nav/links/${link.id}`, { sort_order: other.sort_order })
    await api.put(`/nav/links/${other.id}`, { sort_order: link.sort_order })
    await loadData()
  } catch (e) {
    error.value = e.response?.data?.detail || '调整排序失败'
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
        <div class="flex shrink-0 gap-2">
          <button
            class="rounded border border-hairline bg-card px-3 py-2 text-sm hover:border-teal hover:text-teal"
            @click="openCategoryModal()"
          >
            新建分类
          </button>
          <button
            class="rounded bg-teal px-3 py-2 text-sm text-white hover:bg-teal-dark"
            @click="openLinkModal()"
          >
            新建链接
          </button>
        </div>
      </div>
    </header>

    <p v-if="error" class="mb-4 rounded bg-red-soft px-3 py-2 text-sm text-red">{{ error }}</p>
    <p v-if="loading" class="text-sm text-sub">加载中…</p>
    <p v-else-if="!filteredCategories.length" class="text-sm text-sub">暂无导航内容，先新建一个分类吧。</p>

    <section v-if="pinnedLinks.length" class="mb-8">
      <div class="mb-3 flex items-center gap-2">
        <h3 class="font-serif text-lg font-bold text-ink">常用</h3>
        <span class="rounded-full bg-paper-soft px-2 py-0.5 text-xs text-sub">{{ pinnedLinks.length }}</span>
      </div>
      <div class="flex gap-2.5 overflow-x-auto pb-2">
        <a
          v-for="link in pinnedLinks"
          :key="link.id"
          :href="link.url"
          target="_blank"
          rel="noopener"
          class="flex shrink-0 items-center gap-2 rounded-full border border-hairline bg-card py-1.5 pl-1.5 pr-4 text-sm font-semibold hover:border-teal hover:bg-teal-soft"
        >
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
          <span class="max-w-40 truncate">{{ link.title }}</span>
        </a>
      </div>
    </section>

    <section
      v-for="category in filteredCategories"
      :key="category.id"
      class="mb-7 border-t border-dashed border-hairline pt-4"
    >
      <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div class="flex items-baseline gap-2">
          <h3 class="font-serif text-lg font-bold text-ink">{{ category.name }}</h3>
          <span class="rounded-full bg-paper-soft px-2 py-0.5 text-xs text-sub">{{ category.links.length }}</span>
        </div>
        <div class="flex gap-3 text-sm">
          <button class="text-teal hover:underline" @click="openLinkModal(category)">添加链接</button>
          <button class="text-sub hover:underline" @click="openCategoryModal(category)">重命名</button>
          <button class="text-red hover:underline" @click="deleteCategory(category)">删除</button>
        </div>
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
          <span
            class="actions absolute right-1.5 top-1.5 hidden items-center gap-0.5 rounded-md border border-hairline bg-card px-1 py-0.5 text-[11px] group-hover:flex group-focus-within:flex"
          >
            <button class="text-sub hover:text-ink" title="上移" @click="moveLink(category, link, -1)">↑</button>
            <button class="text-sub hover:text-ink" title="下移" @click="moveLink(category, link, 1)">↓</button>
            <button
              class="hover:text-amber"
              :class="link.is_pinned ? 'text-amber' : 'text-sub'"
              :title="link.is_pinned ? '取消置顶' : '置顶'"
              @click="togglePin(link)"
            >
              ★
            </button>
            <button class="text-sub hover:text-teal" title="编辑" @click="openLinkModal(category, link)">✎</button>
            <button class="text-sub hover:text-red" title="删除" @click="deleteLink(link)">删</button>
          </span>
        </li>
      </ul>
      <p v-else class="py-2 text-sm text-sub">该分类下暂无链接</p>
    </section>

    <div v-if="modal.visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="closeModal">
      <div class="w-full max-w-md rounded-lg bg-card p-6 shadow-xl">
        <h3 class="mb-4 text-lg font-semibold">{{ modal.editing ? '编辑' : '新建' }}{{ modal.type === 'category' ? '分类' : '链接' }}</h3>

        <form v-if="modal.type === 'category'" @submit.prevent="saveCategory">
          <label class="mb-1 block text-sm text-sub">分类名称</label>
          <input v-model="categoryForm.name" type="text" required class="mb-4 w-full rounded border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" />
          <div class="flex justify-end gap-2">
            <button type="button" class="rounded border border-hairline px-4 py-2 text-sm" @click="closeModal">取消</button>
            <button type="submit" class="rounded bg-teal px-4 py-2 text-sm text-white hover:bg-teal-dark">保存</button>
          </div>
        </form>

        <form v-else @submit.prevent="saveLink">
          <label class="mb-1 block text-sm text-sub">标题</label>
          <input v-model="linkForm.title" type="text" required class="mb-3 w-full rounded border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" />
          <label class="mb-1 block text-sm text-sub">URL</label>
          <input v-model="linkForm.url" type="url" required class="mb-3 w-full rounded border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" />
          <label class="mb-1 block text-sm text-sub">描述</label>
          <input v-model="linkForm.description" type="text" class="mb-3 w-full rounded border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none" />
          <label class="mb-1 block text-sm text-sub">分类</label>
          <select v-model="linkForm.category_id" class="mb-3 w-full rounded border border-hairline px-3 py-2 text-sm focus:border-teal focus:outline-none">
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>
          <label class="mb-4 flex items-center gap-2 text-sm text-sub">
            <input v-model="linkForm.is_pinned" type="checkbox" /> 置顶
          </label>
          <div class="flex justify-end gap-2">
            <button type="button" class="rounded border border-hairline px-4 py-2 text-sm" @click="closeModal">取消</button>
            <button type="submit" class="rounded bg-teal px-4 py-2 text-sm text-white hover:bg-teal-dark">保存</button>
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
.actions button {
  padding: 0 3px;
  line-height: 1.4;
}
</style>
