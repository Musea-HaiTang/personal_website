<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

import { useNotesStore } from '../stores/notes'
import { useQuizStore } from '../stores/quiz'

const notesStore = useNotesStore()
const quizStore = useQuizStore()

/* ---------- 页签 ---------- */
const tabs = [
  { key: 'notes', label: '学习笔记' },
  { key: 'qa', label: '问答' },
  { key: 'quiz', label: '答题' }
]
const activeTab = ref('notes')

/* ---------- 笔记列表 ---------- */
const chips = computed(() => [
  { folder: 'all', name: '全部', count: notesStore.notes.length },
  ...notesStore.folders.map((f) => ({ folder: f.folder, name: f.folder, count: f.count }))
])

function excerpt(content, limit = 90) {
  const plain = (content || '').replace(/\s+/g, ' ').trim()
  return plain.length <= limit ? plain : plain.slice(0, limit) + '…'
}
function fmtDate(ts) {
  return String(ts || '').slice(0, 10)
}

/* ---------- 阅读/编辑弹窗 ---------- */
const readerId = ref(null)
const editTitle = ref('')
const editTags = ref([])
const editContent = ref('')
const dirty = ref(false)
const savedMsg = ref('')
const tagInputOpen = ref(false)
const newTag = ref('')
const saving = ref(false)

const readerOpen = computed(() => readerId.value !== null)

function openReader(note) {
  readerId.value = note.id
  editTitle.value = note.title
  editTags.value = [...(note.tags || [])]
  editContent.value = note.content || ''
  dirty.value = false
  savedMsg.value = ''
  tagInputOpen.value = false
}
function closeReader() {
  if (dirty.value && !window.confirm('有未保存的修改，确定关闭？修改将丢失。')) return
  readerId.value = null
  dirty.value = false
}
function markDirty() {
  dirty.value = true
  savedMsg.value = ''
}
async function saveNote() {
  if (readerId.value === null || saving.value) return
  saving.value = true
  try {
    await notesStore.update(readerId.value, {
      title: editTitle.value.trim() || '无标题',
      tags: editTags.value,
      content: editContent.value
    })
    dirty.value = false
    savedMsg.value = '已保存'
    await notesStore.refresh()
  } catch (e) {
    savedMsg.value = e.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}
async function deleteNote() {
  if (readerId.value === null) return
  if (!window.confirm('确定删除这篇笔记？正文文件也会被删除。')) return
  try {
    await notesStore.remove(readerId.value)
    readerId.value = null
    dirty.value = false
    await notesStore.refresh()
  } catch (e) {
    savedMsg.value = e.response?.data?.detail || '删除失败'
  }
}
function addTag() {
  const v = newTag.value.trim()
  if (!v) return
  if (!editTags.value.includes(v)) {
    editTags.value.push(v)
    markDirty()
  }
  newTag.value = ''
  tagInputOpen.value = false
}
function removeTag(t) {
  editTags.value = editTags.value.filter((x) => x !== t)
  markDirty()
}

function beforeUnload(e) {
  if (dirty.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}
function onKeydown(e) {
  if (readerOpen.value && (e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault()
    saveNote()
  }
}
onMounted(() => {
  if (!notesStore.loaded) notesStore.refresh()
  window.addEventListener('keydown', onKeydown)
  window.addEventListener('beforeunload', beforeUnload)
})
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  window.removeEventListener('beforeunload', beforeUnload)
})
onBeforeRouteLeave(() => {
  if (dirty.value) return window.confirm('有未保存的修改，离开将丢失，确定离开？')
  return true
})

/* ---------- 导入弹窗 ---------- */
const importOpen = ref(false)
const importTab = ref('paste')
const pTitle = ref('')
const pTags = ref('')
const pContent = ref('')
const folderSel = ref('未分类')
const folderNew = ref('')
const uploadFiles = ref([])
const dirFiles = ref([])
const importMsg = ref('')
const importing = ref(false)

const folderOptions = computed(() => ['未分类', ...notesStore.folders.map((f) => f.folder)])
const targetFolder = computed(() => folderNew.value.trim() || folderSel.value)

function openImport() {
  importOpen.value = true
  importTab.value = 'paste'
  importMsg.value = ''
  uploadFiles.value = []
  dirFiles.value = []
}
function onUploadChange(e) {
  uploadFiles.value = [...e.target.files]
}
function onDirChange(e) {
  dirFiles.value = [...e.target.files]
}
async function doPaste() {
  const title = pTitle.value.trim()
  if (!title) {
    importMsg.value = '请填写笔记标题'
    return
  }
  importing.value = true
  importMsg.value = ''
  try {
    await notesStore.create({
      title,
      folder: targetFolder.value,
      tags: pTags.value.split(/[,，]/).map((t) => t.trim()).filter(Boolean),
      content: pContent.value
    })
    importMsg.value = '已创建笔记'
    pTitle.value = ''
    pTags.value = ''
    pContent.value = ''
    await notesStore.refresh()
  } catch (e) {
    importMsg.value = e.response?.data?.detail || '创建失败'
  } finally {
    importing.value = false
  }
}
async function doImport(files) {
  if (!files.length) {
    importMsg.value = '请先选择 .md 文件'
    return
  }
  importing.value = true
  importMsg.value = ''
  try {
    const result = await notesStore.importFiles(targetFolder.value, files)
    const parts = [`已导入 ${result.created.length} 篇`]
    if (result.renamed.length) parts.push(`自动改名：${result.renamed.join('、')}`)
    if (result.errors.length) parts.push(`失败：${result.errors.join('；')}`)
    importMsg.value = parts.join('；')
    uploadFiles.value = []
    dirFiles.value = []
    await notesStore.refresh()
  } catch (e) {
    importMsg.value = e.response?.data?.detail || '导入失败'
  } finally {
    importing.value = false
  }
}

/* ---------- 题库管理弹窗（P1-04） ---------- */
const manageOpen = ref(false)
const preview = ref(null)
const manageMsg = ref('')
const managing = ref(false)

const YAML_SAMPLE = `# 分类固定写在文件顶部，整个文件一个分类
category: Python
questions:
  - type: choice          # choice=选择题（考概念）
    no: "1.1"
    score: 5
    title: 下面哪个是 Python 装饰器的正确理解？
    options:              # 固定 4 项，对应 A/B/C/D
      - 装饰器是接收函数并返回新函数的可调用对象   # A
      - 装饰器只能修饰类方法                      # B
      - 被 @ 装饰的函数会立即执行                 # C
      - 装饰器是 Python 3 才有的特性              # D
    answer: A             # 只能填 A/B/C/D 之一
    explanation: |
      装饰器本质是接收函数并返回新函数的可调用对象。

  - type: fill            # fill=填空题（考代码挖空）
    no: "1.2"
    score: 10
    title: 补全装饰器：返回内部函数
    code: |
      def timer(fn):
          def wrap(*a, **kw):
              return fn(*a, **kw)
          return ____
    answer: wrap
    explanation: |
      装饰器要把 wrap 返回出去替换原函数。`

function openManage() {
  manageOpen.value = true
  preview.value = null
  manageMsg.value = ''
}
async function onQuizFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  manageMsg.value = ''
  preview.value = null
  try {
    preview.value = await quizStore.previewImport(file)
  } catch (err) {
    manageMsg.value = err.response?.data?.detail || '解析失败'
  } finally {
    e.target.value = ''
  }
}
async function confirmImport() {
  if (!preview.value || !preview.value.items.length || managing.value) return
  managing.value = true
  try {
    const result = await quizStore.confirmImport(preview.value.items)
    manageMsg.value = `导入成功：新增 ${result.imported} 题、更新 ${result.updated} 题`
    preview.value = null
    quizStore.refresh()
  } catch (err) {
    manageMsg.value = err.response?.data?.detail || '导入失败'
  } finally {
    managing.value = false
  }
}
</script>

<template>
  <div class="flex h-full flex-col gap-4">
    <!-- 页签 -->
    <div class="flex items-center justify-between">
      <h1 class="font-serif text-2xl tracking-wide text-ink">笔记</h1>
      <div class="flex gap-1 rounded-xl bg-paper-soft p-1">
        <button
          v-for="t in tabs"
          :key="t.key"
          class="rounded-lg px-5 py-1.5 text-sm text-sub"
          :class="{ 'bg-card font-semibold text-teal shadow-sm': activeTab === t.key }"
          @click="activeTab = t.key"
        >
          {{ t.label }}
        </button>
      </div>
    </div>

    <!-- 学习笔记 -->
    <template v-if="activeTab === 'notes'">
      <div class="flex items-center gap-3">
        <input
          v-model="notesStore.kw"
          class="w-80 rounded-lg border border-hairline bg-card px-3.5 py-2 text-sm text-ink placeholder:text-sub focus:border-teal focus:outline-none"
          placeholder="全文检索：标题、正文、标签…"
        >
        <button
          class="rounded-full border border-teal bg-teal px-4 py-1.5 text-sm font-medium text-card hover:bg-teal-dark"
          @click="openImport"
        >
          ＋ 导入笔记
        </button>
      </div>

      <div class="flex flex-wrap gap-2">
        <button
          v-for="c in chips"
          :key="c.folder"
          class="rounded-full border px-3.5 py-1 text-[13px]"
          :class="notesStore.folder === c.folder
            ? 'border-teal bg-teal text-card'
            : 'border-hairline bg-card text-ink hover:border-teal'"
          @click="notesStore.folder = c.folder"
        >
          {{ c.name }}<span class="ml-1.5 text-xs opacity-70">{{ c.count }}</span>
        </button>
      </div>

      <p v-if="notesStore.error" class="text-sm text-red">{{ notesStore.error }}</p>
      <div
        v-if="!notesStore.loaded || notesStore.notes.length === 0"
        class="rounded-xl border border-dashed border-hairline bg-card p-10 text-center text-sm text-sub"
      >
        还没有笔记，点「＋ 导入笔记」粘贴新建或上传 .md 文件。
      </div>
      <div v-else class="grid grid-cols-[repeat(auto-fill,minmax(240px,1fr))] gap-3">
        <button
          v-for="n in notesStore.filtered"
          :key="n.id"
          class="flex flex-col gap-1.5 rounded-xl border border-hairline bg-card p-4 text-left hover:border-teal"
          @click="openReader(n)"
        >
          <span class="font-medium text-ink">{{ n.title }}</span>
          <span class="line-clamp-2 text-[12.5px] leading-relaxed text-sub">{{ excerpt(n.content) }}</span>
          <span class="text-[11px] text-sub">{{ fmtDate(n.updated_at) }} · {{ n.folder }}</span>
          <span class="flex flex-wrap gap-1">
            <span
              v-for="t in n.tags"
              :key="t"
              class="rounded-full bg-teal-soft px-2 py-px text-[11px] text-teal-dark"
            >
              {{ t }}
            </span>
          </span>
        </button>
      </div>
    </template>

    <!-- 问答 -->
    <div v-else-if="activeTab === 'qa'" class="rounded-xl border border-dashed border-hairline bg-card p-12 text-center text-sm text-sub">
      问答功能开发中（P1-03：基于笔记的 RAG 问答）
    </div>

    <!-- 答题 -->
    <div v-else class="flex flex-col gap-4">
      <div class="flex items-center justify-between">
        <h2 class="font-serif text-lg text-ink">技术答题</h2>
        <button class="rounded-lg border border-hairline bg-card px-4 py-1.5 text-sm hover:border-teal hover:text-teal" @click="openManage">
          题库管理
        </button>
      </div>
      <div class="rounded-xl border border-dashed border-hairline bg-card p-12 text-center text-sm text-sub">
        答题功能开发中（P1-05：选择题 / 填空题判分）
      </div>
    </div>

    <!-- 阅读/编辑弹窗 -->
    <div v-if="readerOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/35 p-6" @click.self="closeReader">
      <div class="letter flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden">
        <div class="flex items-start gap-3">
          <input
            v-model="editTitle"
            class="flex-1 bg-transparent font-serif text-2xl font-bold text-ink focus:outline-none"
            placeholder="无标题"
            @input="markDirty"
          >
          <div class="flex gap-1.5">
            <button class="rounded-lg p-1.5 text-sub hover:bg-teal-soft hover:text-teal" title="删除" @click="deleteNote">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="h-4 w-4">
                <path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13M10 11v5M14 11v5" />
              </svg>
            </button>
            <button class="rounded-lg p-1.5 text-sub hover:bg-teal-soft hover:text-teal" title="关闭" @click="closeReader">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="h-4 w-4">
                <path d="M6 6l12 12M18 6L6 18" />
              </svg>
            </button>
          </div>
        </div>
        <div class="mt-1 flex items-center gap-2 text-xs text-sub">
          <span>{{ readerNote.folder }} · {{ fmtDate(readerNote.updated_at) }}</span>
          <span v-if="dirty" class="text-amber">● 未保存（Ctrl+S 保存）</span>
          <span v-else-if="savedMsg" class="text-teal">✓ {{ savedMsg }}</span>
        </div>
        <div class="mt-2 flex flex-wrap items-center gap-1.5">
          <button
            v-for="t in editTags"
            :key="t"
            class="rounded-full bg-teal-soft px-2.5 py-px text-xs text-teal-dark hover:bg-teal hover:text-card"
            @click="removeTag(t)"
          >
            {{ t }}<span class="ml-1 opacity-50">✕</span>
          </button>
          <button v-if="!tagInputOpen" class="rounded-full border border-dashed border-teal px-2.5 py-px text-xs text-teal-dark" @click="tagInputOpen = true">
            ＋ 标签
          </button>
          <input
            v-if="tagInputOpen"
            v-model="newTag"
            class="w-24 rounded-full border border-hairline bg-card px-2.5 py-px text-xs focus:border-teal focus:outline-none"
            placeholder="回车添加"
            @keydown.enter.prevent="addTag"
            @keydown.esc="tagInputOpen = false"
          >
        </div>
        <textarea
          v-model="editContent"
          class="mt-3 min-h-[240px] flex-1 resize-none bg-transparent text-sm leading-7 text-ink focus:outline-none"
          placeholder="支持 Markdown，例如：## 标题、`代码`…"
          spellcheck="false"
          @input="markDirty"
        />
      </div>
    </div>

    <!-- 导入弹窗 -->
    <div v-if="importOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/35 p-6" @click.self="importOpen = false">
      <div class="w-full max-w-md rounded-2xl border border-hairline bg-card p-6 shadow-xl">
        <h3 class="mb-3 font-serif text-lg text-ink">导入笔记</h3>
        <div class="mb-4 flex gap-1 rounded-xl bg-paper-soft p-1">
          <button
            v-for="t in [['paste', '粘贴新建'], ['upload', '上传文件'], ['folder', '批量导入文件夹']]"
            :key="t[0]"
            class="flex-1 rounded-lg py-1.5 text-sm"
            :class="importTab === t[0] ? 'bg-card font-semibold text-teal shadow-sm' : 'text-sub'"
            @click="importTab = t[0]"
          >
            {{ t[1] }}
          </button>
        </div>

        <div class="mb-3 flex gap-2">
          <select v-model="folderSel" class="flex-1 rounded-lg border border-hairline bg-card px-2.5 py-2 text-sm focus:border-teal focus:outline-none">
            <option v-for="f in folderOptions" :key="f" :value="f">{{ f }}</option>
          </select>
          <input v-model="folderNew" class="flex-1 rounded-lg border border-hairline bg-card px-2.5 py-2 text-sm placeholder:text-sub focus:border-teal focus:outline-none" placeholder="新文件夹（可选）">
        </div>

        <template v-if="importTab === 'paste'">
          <input v-model="pTitle" class="mb-2 w-full rounded-lg border border-hairline bg-card px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="笔记标题">
          <input v-model="pTags" class="mb-2 w-full rounded-lg border border-hairline bg-card px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="标签（逗号分隔，可选）">
          <textarea v-model="pContent" class="h-36 w-full resize-none rounded-lg border border-hairline bg-card px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="正文（Markdown）" />
        </template>
        <template v-else-if="importTab === 'upload'">
          <label class="block cursor-pointer rounded-xl border border-dashed border-hairline p-8 text-center text-sm text-sub hover:border-teal hover:text-teal">
            点击选择或拖拽 .md 文件（可多选）
            <input type="file" multiple accept=".md,.markdown,.txt" class="hidden" @change="onUploadChange">
          </label>
          <p v-if="uploadFiles.length" class="mt-2 text-xs text-sub">已选择 {{ uploadFiles.length }} 个文件</p>
        </template>
        <template v-else>
          <label class="block cursor-pointer rounded-xl border border-dashed border-hairline p-8 text-center text-sm text-sub hover:border-teal hover:text-teal">
            选择一个本地文件夹，批量导入其中的 .md 文件
            <input type="file" webkitdirectory multiple class="hidden" @change="onDirChange">
          </label>
          <p v-if="dirFiles.length" class="mt-2 text-xs text-sub">已选择 {{ dirFiles.length }} 个文件（按所选文件夹归入）</p>
        </template>

        <p v-if="importMsg" class="mt-3 text-xs text-teal-dark">{{ importMsg }}</p>
        <div class="mt-4 flex justify-end gap-2">
          <button class="rounded-lg border border-hairline px-4 py-1.5 text-sm hover:border-teal hover:text-teal" @click="importOpen = false">取消</button>
          <button
            class="rounded-lg bg-teal px-4 py-1.5 text-sm font-medium text-card hover:bg-teal-dark disabled:opacity-50"
            :disabled="importing"
            @click="importTab === 'paste' ? doPaste() : importTab === 'upload' ? doImport(uploadFiles) : doImport(dirFiles)"
          >
            {{ importing ? '处理中…' : '导入' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 题库管理弹窗 -->
    <div v-if="manageOpen" class="fixed inset-0 z-50 flex items-center justify-center bg-ink/35 p-6" @click.self="manageOpen = false">
      <div class="flex max-h-[85vh] w-full max-w-xl flex-col rounded-2xl border border-hairline bg-card p-6 shadow-xl">
        <h3 class="mb-2 font-serif text-lg text-ink">题库管理</h3>
        <p class="mb-3 text-[13px] text-sub">
          让 AI 按固定格式生成题目后快速导入。分类写在文件顶部，整个文件一个分类；选择题考概念、填空题考代码挖空。
        </p>
        <pre class="min-h-0 flex-1 overflow-auto rounded-lg border border-hairline bg-paper-soft p-3 text-xs leading-relaxed">{{ YAML_SAMPLE }}</pre>
        <div class="mt-3 flex flex-wrap gap-2">
          <label class="cursor-pointer rounded-lg bg-teal px-4 py-2 text-sm font-medium text-card hover:bg-teal-dark">
            导入题目
            <input type="file" accept=".yaml,.yml,.md,.txt" class="hidden" @change="onQuizFile">
          </label>
          <button class="rounded-lg border border-hairline px-4 py-2 text-sm hover:border-teal hover:text-teal" @click="quizStore.downloadTemplate()">
            下载题目格式文档
          </button>
          <button class="rounded-lg border border-hairline px-4 py-2 text-sm hover:border-teal hover:text-teal" @click="manageOpen = false">关闭</button>
        </div>

        <div v-if="preview" class="mt-3 rounded-lg bg-paper-soft p-3 text-[13px]">
          <p>分类：<span class="font-medium text-teal-dark">{{ preview.category || '—' }}</span></p>
          <p>新增 {{ preview.new.length }} 题、更新 {{ preview.updated.length }} 题</p>
          <p v-if="preview.errors.length" class="text-red">错误：{{ preview.errors.join('；') }}</p>
          <button
            v-if="preview.items.length"
            class="mt-2 rounded-lg bg-teal px-4 py-1.5 text-sm font-medium text-card hover:bg-teal-dark disabled:opacity-50"
            :disabled="managing"
            @click="confirmImport"
          >
            {{ managing ? '导入中…' : '确认导入 ' + preview.items.length + ' 题' }}
          </button>
        </div>
        <p v-if="manageMsg" class="mt-3 text-xs text-teal-dark">{{ manageMsg }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.letter {
  background: #f4f9f6;
  border: 1px solid #cfe5dc;
  border-radius: 8px;
  box-shadow: 0 16px 40px rgba(43, 38, 34, 0.18);
  padding: 30px 36px;
}
.letter textarea {
  background-image: repeating-linear-gradient(transparent, transparent 27px, #e2ece7 27px, #e2ece7 28px);
  background-attachment: local;
  line-height: 28px;
}
.letter ::-webkit-scrollbar,
pre::-webkit-scrollbar {
  width: 6px;
}
.letter ::-webkit-scrollbar-track,
pre::-webkit-scrollbar-track {
  background: transparent;
}
.letter ::-webkit-scrollbar-thumb,
pre::-webkit-scrollbar-thumb {
  background: #2b2622;
  border-radius: 999px;
}
</style>
