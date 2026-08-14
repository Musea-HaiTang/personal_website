<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import MarkdownIt from 'markdown-it'
import api from '../api'

const md = new MarkdownIt()

const entries = ref([])
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const search = reactive({ q: '', tag: '', day: '' })

const form = reactive({ id: null, date: '', title: '', tags: '', content: '' })

const previewHtml = computed(() => md.render(form.content || ''))

function today() {
  const now = new Date()
  const offset = now.getTimezoneOffset()
  return new Date(now.getTime() - offset * 60000).toISOString().slice(0, 10)
}

function resetForm() {
  form.id = null
  form.date = today()
  form.title = ''
  form.tags = ''
  form.content = ''
}

async function loadEntries() {
  loading.value = true
  error.value = ''
  try {
    const params = {}
    if (search.q.trim()) params.q = search.q.trim()
    if (search.tag.trim()) params.tag = search.tag.trim()
    if (search.day) params.day = search.day
    const { data } = await api.get('/diary', { params })
    entries.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || '加载日记失败'
  } finally {
    loading.value = false
  }
}

function selectEntry(entry) {
  form.id = entry.id
  form.date = entry.date
  form.title = entry.title
  form.tags = (entry.tags || []).join(', ')
  form.content = entry.content || ''
}

async function saveDiary() {
  if (!form.date || !form.title.trim()) {
    error.value = '日期和标题不能为空'
    return
  }
  saving.value = true
  error.value = ''
  const payload = {
    date: form.date,
    title: form.title.trim(),
    tags: form.tags.split(/[,，]/).map((s) => s.trim()).filter(Boolean),
    content: form.content
  }
  try {
    if (form.id) {
      await api.put(`/diary/${form.id}`, payload)
    } else {
      await api.post('/diary', payload)
    }
    await loadEntries()
    const saved = entries.value.find((e) => e.date === form.date)
    if (saved) selectEntry(saved)
    else resetForm()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存日记失败'
  } finally {
    saving.value = false
  }
}

async function deleteDiary() {
  if (!form.id) return
  if (!confirm(`确定删除 ${form.date} 的日记？正文文件也会被删除。`)) return
  try {
    await api.delete(`/diary/${form.id}`)
    resetForm()
    await loadEntries()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除日记失败'
  }
}

async function newDiary() {
  if (form.id && form.content && !confirm('当前有未保存的编辑内容，新建会丢弃，确定继续？')) return
  resetForm()
}

onMounted(async () => {
  resetForm()
  await loadEntries()
})
</script>

<template>
  <div>
    <div class="mb-6 flex items-center justify-between">
      <h2 class="text-2xl font-bold">日记</h2>
      <button class="rounded bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700" @click="newDiary">新建日记</button>
    </div>

    <div class="mb-4 flex flex-wrap gap-2">
      <input v-model="search.q" type="text" placeholder="关键词搜索" class="w-48 rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" @input="loadEntries" />
      <input v-model="search.tag" type="text" placeholder="按标签筛选" class="w-40 rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" @input="loadEntries" />
      <input v-model="search.day" type="date" class="rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" @change="loadEntries" />
      <button v-if="search.q || search.tag || search.day" class="text-sm text-gray-500 hover:underline" @click="search.q = ''; search.tag = ''; search.day = ''; loadEntries()">清除筛选</button>
    </div>

    <p v-if="error" class="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-600">{{ error }}</p>

    <div class="grid grid-cols-1 gap-6 lg:grid-cols-[280px_1fr]">
      <aside>
        <p v-if="loading" class="text-sm text-gray-500">加载中…</p>
        <p v-else-if="!entries.length" class="text-sm text-gray-500">暂无日记</p>
        <ul v-else class="space-y-2">
          <li
            v-for="entry in entries"
            :key="entry.id"
            class="cursor-pointer rounded border border-gray-200 bg-white px-3 py-2 hover:border-blue-300"
            :class="{ 'border-blue-500': form.id === entry.id }"
            @click="selectEntry(entry)"
          >
            <p class="truncate text-sm font-medium">{{ entry.title }}</p>
            <p class="text-xs text-gray-400">{{ entry.date }}</p>
            <p v-if="entry.tags.length" class="mt-1 flex flex-wrap gap-1">
              <span v-for="tag in entry.tags" :key="tag" class="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500">{{ tag }}</span>
            </p>
          </li>
        </ul>
      </aside>

      <div class="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div class="border-b border-gray-100 p-4">
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div>
              <label class="mb-1 block text-sm text-gray-600">日期</label>
              <input v-model="form.date" type="date" class="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
            </div>
            <div class="sm:col-span-2">
              <label class="mb-1 block text-sm text-gray-600">标题</label>
              <input v-model="form.title" type="text" class="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
            </div>
          </div>
          <div class="mt-3">
            <label class="mb-1 block text-sm text-gray-600">标签（逗号分隔）</label>
            <input v-model="form.tags" type="text" placeholder="生活, 工作" class="w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2">
          <div class="border-b border-gray-100 md:border-b-0 md:border-r">
            <p class="border-b border-gray-100 px-4 py-2 text-xs font-medium text-gray-400">编辑</p>
            <textarea v-model="form.content" rows="18" placeholder="用 Markdown 写日记…" class="w-full resize-y bg-transparent px-4 py-3 text-sm focus:outline-none"></textarea>
          </div>
          <div>
            <p class="border-b border-gray-100 px-4 py-2 text-xs font-medium text-gray-400">预览</p>
            <div class="prose prose-sm max-w-none px-4 py-3 text-sm" v-html="previewHtml"></div>
          </div>
        </div>

        <div class="flex justify-end gap-2 border-t border-gray-100 p-4">
          <button v-if="form.id" class="rounded border border-red-200 px-4 py-2 text-sm text-red-600 hover:bg-red-50" @click="deleteDiary">删除</button>
          <button class="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700" :disabled="saving" @click="saveDiary">
            {{ saving ? '保存中…' : form.id ? '保存修改' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
