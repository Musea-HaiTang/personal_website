<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import api from '../api'

const tasks = ref([])
const filterDate = ref('')
const loading = ref(false)
const error = ref('')

const modal = reactive({ visible: false, editing: null })
const form = reactive({ title: '', date: '', priority: 2, note: '' })

const priorityLabels = { 1: '低', 2: '中', 3: '高' }
const priorityColors = { 1: 'bg-gray-100 text-gray-600', 2: 'bg-blue-50 text-blue-600', 3: 'bg-red-50 text-red-600' }

async function loadTasks() {
  loading.value = true
  error.value = ''
  try {
    const params = filterDate.value ? { date: filterDate.value } : {}
    const { data } = await api.get('/tasks', { params })
    tasks.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || '加载任务失败'
  } finally {
    loading.value = false
  }
}

const groupedTasks = computed(() => {
  const groups = {}
  for (const task of tasks.value) {
    if (!groups[task.date]) groups[task.date] = []
    groups[task.date].push(task)
  }
  return Object.keys(groups)
    .sort()
    .map((date) => ({ date, items: groups[date] }))
})

function today() {
  const now = new Date()
  const offset = now.getTimezoneOffset()
  return new Date(now.getTime() - offset * 60000).toISOString().slice(0, 10)
}

function openModal(task = null) {
  modal.editing = task
  form.title = task ? task.title : ''
  form.date = task ? task.date : today()
  form.priority = task ? task.priority : 2
  form.note = task ? task.note || '' : ''
  modal.visible = true
}

function closeModal() {
  modal.visible = false
}

async function saveTask() {
  if (!form.title.trim() || !form.date) return
  const payload = {
    title: form.title.trim(),
    date: form.date,
    priority: Number(form.priority),
    note: form.note.trim() || null
  }
  try {
    if (modal.editing) {
      await api.put(`/tasks/${modal.editing.id}`, payload)
    } else {
      await api.post('/tasks', payload)
    }
    closeModal()
    await loadTasks()
  } catch (e) {
    error.value = e.response?.data?.detail || '保存任务失败'
  }
}

async function deleteTask(task) {
  if (!confirm(`确定删除任务「${task.title}」？`)) return
  try {
    await api.delete(`/tasks/${task.id}`)
    await loadTasks()
  } catch (e) {
    error.value = e.response?.data?.detail || '删除任务失败'
  }
}

async function toggleCompleted(task) {
  try {
    await api.put(`/tasks/${task.id}`, { completed: !task.completed })
    await loadTasks()
  } catch (e) {
    error.value = e.response?.data?.detail || '切换状态失败'
  }
}

function formatDate(dateStr) {
  const date = new Date(dateStr + 'T00:00:00')
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  return `${dateStr} 周${weekdays[date.getDay()]}`
}

onMounted(loadTasks)
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-3">
      <h2 class="text-2xl font-bold">计划</h2>
      <div class="flex items-center gap-3">
        <input v-model="filterDate" type="date" class="rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" @change="loadTasks" />
        <button v-if="filterDate" class="text-sm text-gray-500 hover:underline" @click="filterDate = ''; loadTasks()">清除筛选</button>
        <button class="rounded bg-blue-600 px-3 py-2 text-sm text-white hover:bg-blue-700" @click="openModal()">新增任务</button>
      </div>
    </div>

    <p v-if="error" class="mb-4 rounded bg-red-50 px-3 py-2 text-sm text-red-600">{{ error }}</p>
    <p v-if="loading" class="text-sm text-gray-500">加载中…</p>
    <p v-else-if="!groupedTasks.length" class="text-sm text-gray-500">暂无任务，点「新增任务」开始安排吧。</p>

    <div v-for="group in groupedTasks" :key="group.date" class="mb-6">
      <h3 class="mb-2 font-semibold text-gray-700">{{ formatDate(group.date) }}</h3>
      <div class="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
        <div v-for="task in group.items" :key="task.id" class="flex items-center gap-3 border-b border-gray-100 px-4 py-3 last:border-b-0">
          <input
            type="checkbox"
            :checked="task.completed"
            class="h-4 w-4 accent-blue-600"
            @change="toggleCompleted(task)"
          />
          <div class="min-w-0 flex-1">
            <p :class="task.completed ? 'text-gray-400 line-through' : 'font-medium'" class="truncate">{{ task.title }}</p>
            <p v-if="task.note" class="truncate text-sm text-gray-500">{{ task.note }}</p>
          </div>
          <span class="shrink-0 rounded px-2 py-0.5 text-xs" :class="priorityColors[task.priority]">优先级{{ priorityLabels[task.priority] }}</span>
          <div class="flex shrink-0 gap-2 text-sm">
            <button class="text-blue-600 hover:underline" @click="openModal(task)">编辑</button>
            <button class="text-red-500 hover:underline" @click="deleteTask(task)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="modal.visible" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30" @click.self="closeModal">
      <div class="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h3 class="mb-4 text-lg font-semibold">{{ modal.editing ? '编辑任务' : '新增任务' }}</h3>
        <form @submit.prevent="saveTask">
          <label class="mb-1 block text-sm text-gray-600">标题</label>
          <input v-model="form.title" type="text" required class="mb-3 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
          <label class="mb-1 block text-sm text-gray-600">日期</label>
          <input v-model="form.date" type="date" required class="mb-3 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
          <label class="mb-1 block text-sm text-gray-600">优先级</label>
          <select v-model="form.priority" class="mb-3 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none">
            <option :value="1">低</option>
            <option :value="2">中</option>
            <option :value="3">高</option>
          </select>
          <label class="mb-1 block text-sm text-gray-600">备注</label>
          <textarea v-model="form.note" rows="3" class="mb-4 w-full rounded border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"></textarea>
          <div class="flex justify-end gap-2">
            <button type="button" class="rounded border border-gray-300 px-4 py-2 text-sm" @click="closeModal">取消</button>
            <button type="submit" class="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700">保存</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>
