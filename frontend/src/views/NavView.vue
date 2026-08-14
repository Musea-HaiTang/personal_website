<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from '../api'

const categories = ref([])
const keyword = ref('')
const loading = ref(false)
const error = ref('')

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
          (link.description || '').toLowerCase().includes(kw)
      )
    }))
    .filter((cat) => cat.links.length > 0)
})

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
    <div class="mb-6 flex items-center justify-between">
      <h2 class="text-2xl font-bold">导航</h2>
      <button class="rounded bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700" @click="openCategoryModal()">
        新建分类
      </button>
    </div>

    <input
      v-model="keyword"
      type="text"
      placeholder="搜索标题、URL 或描述…"
      class="mb-6 w-full max-w-md rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
    />

    <p v-if="error" class="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-600">{{ error }}</p>
    <p v-if="loading" class="text-sm text-gray-500">加载中…</p>
    <p v-else-if="!filteredCategories.length" class="text-sm text-gray-500">暂无导航内容，先新建一个分类吧。</p>

    <div v-for="category in filteredCategories" :key="category.id" class="mb-6 rounded-lg border border-gray-200 bg-white shadow-sm">
      <div class="flex items-center justify-between border-b border-gray-100 px-4 py-3">
        <h3 class="font-semibold">{{ category.name }}</h3>
        <div class="flex gap-2">
          <button class="text-sm text-blue-600 hover:underline" @click="openLinkModal(category)">添加链接</button>
          <button class="text-sm text-gray-500 hover:underline" @click="openCategoryModal(category)">重命名</button>
          <button class="text-sm text-red-500 hover:underline" @click="deleteCategory(category)">删除</button>
        </div>
      </div>
      <ul v-if="category.links.length" class="divide-y divide-gray-100">
        <li v-for="link in category.links" :key="link.id" class="flex items-center gap-3 px-4 py-3">
          <span :class="link.is_pinned ? 'text-amber-500' : 'text-gray-300'" title="置顶">★</span>
          <div class="min-w-0 flex-1">
            <a :href="link.url" target="_blank" rel="noopener" class="font-medium text-blue-600 hover:underline">{{ link.title }}</a>
            <p v-if="link.description" class="truncate text-sm text-gray-500">{{ link.description }}</p>
            <p class="truncate text-xs text-gray-400">{{ link.url }}</p>
          </div>
          <div class="flex shrink-0 items-center gap-2 text-sm">
            <button class="text-gray-500 hover:text-gray-800" title="上移" @click="moveLink(category, link, -1)">↑</button>
            <button class="text-gray-500 hover:text-gray-800" title="下移" @click="moveLink(category, link, 1)">↓</button>
            <button class="text-amber-600 hover:underline" @click="togglePin(link)">{{ link.is_pinned ? '取消置顶' : '置顶' }}</button>
            <button class="text-blue-600 hover:underline" @click="openLinkModal(category, link)">编辑</button>
            <button class="text-red-500 hover:underline" @click="deleteLink(link)">删除</button>
          </div>
        </li>
      </ul>
      <p v-else class="px-4 py-3 text-sm text-gray-400">该分类下暂无链接</p>
    </div>

    <div v-if="modal.visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="closeModal">
      <div class="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 class="mb-4 text-lg font-semibold">{{ modal.editing ? '编辑' : '新建' }}{{ modal.type === 'category' ? '分类' : '链接' }}</h3>

        <form v-if="modal.type === 'category'" @submit.prevent="saveCategory">
          <label class="mb-1 block text-sm text-gray-600">分类名称</label>
          <input v-model="categoryForm.name" type="text" required class="mb-4 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
          <div class="flex justify-end gap-2">
            <button type="button" class="rounded border border-gray-300 px-4 py-2 text-sm" @click="closeModal">取消</button>
            <button type="submit" class="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">保存</button>
          </div>
        </form>

        <form v-else @submit.prevent="saveLink">
          <label class="mb-1 block text-sm text-gray-600">标题</label>
          <input v-model="linkForm.title" type="text" required class="mb-3 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
          <label class="mb-1 block text-sm text-gray-600">URL</label>
          <input v-model="linkForm.url" type="url" required class="mb-3 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
          <label class="mb-1 block text-sm text-gray-600">描述</label>
          <input v-model="linkForm.description" type="text" class="mb-3 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
          <label class="mb-1 block text-sm text-gray-600">分类</label>
          <select v-model="linkForm.category_id" class="mb-3 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>
          <label class="mb-4 flex items-center gap-2 text-sm text-gray-600">
            <input v-model="linkForm.is_pinned" type="checkbox" /> 置顶
          </label>
          <div class="flex justify-end gap-2">
            <button type="button" class="rounded border border-gray-300 px-4 py-2 text-sm" @click="closeModal">取消</button>
            <button type="submit" class="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
