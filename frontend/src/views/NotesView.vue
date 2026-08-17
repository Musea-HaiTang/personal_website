<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

import ImportNotesModal from '../components/notes/ImportNotesModal.vue'
import NoteEditorModal from '../components/notes/NoteEditorModal.vue'
import QuizManageModal from '../components/notes/QuizManageModal.vue'
import { useNotesStore } from '../stores/notes'
import { fmtDate } from '../utils/date'
import { hlHtml } from '../utils/highlight'

const notesStore = useNotesStore()

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

/* ---------- 弹窗编排 ---------- */
const readerId = ref(null)
const editorDirty = ref(false)
const importOpen = ref(false)
const manageOpen = ref(false)

const readerOpen = computed(() => readerId.value !== null)
const readerNote = computed(() => notesStore.notes.find((n) => n.id === readerId.value) || null)

function openReader(note) {
  readerId.value = note.id
  editorDirty.value = false
}
function closeReader() {
  readerId.value = null
}
function onDirtyChange(v) {
  editorDirty.value = v
}
async function onSaved() {
  await notesStore.refresh()
}
async function onRemoved() {
  readerId.value = null
  editorDirty.value = false
  await notesStore.refresh()
}

function beforeUnload(e) {
  if (editorDirty.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}
onMounted(() => {
  if (!notesStore.loaded) notesStore.refresh()
  window.addEventListener('beforeunload', beforeUnload)
})
onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', beforeUnload)
})
onBeforeRouteLeave(() => {
  if (editorDirty.value) return window.confirm('有未保存的修改，离开将丢失，确定离开？')
  return true
})
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
          @click="importOpen = true"
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
          <span class="font-medium text-ink" v-html="hlHtml(n.title, notesStore.kw)"></span>
          <span class="line-clamp-2 text-[12.5px] leading-relaxed text-sub" v-html="hlHtml(excerpt(n.content), notesStore.kw)"></span>
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
        <button class="rounded-lg border border-hairline bg-card px-4 py-1.5 text-sm hover:border-teal hover:text-teal" @click="manageOpen = true">
          题库管理
        </button>
      </div>
      <div class="rounded-xl border border-dashed border-hairline bg-card p-12 text-center text-sm text-sub">
        答题功能开发中（P1-05：选择题 / 填空题判分）
      </div>
    </div>

    <!-- 弹窗 -->
    <NoteEditorModal
      v-if="readerOpen"
      :note="readerNote"
      @close="closeReader"
      @saved="onSaved"
      @removed="onRemoved"
      @dirty-change="onDirtyChange"
    />
    <ImportNotesModal v-if="importOpen" @close="importOpen = false" @imported="onSaved" />
    <QuizManageModal v-if="manageOpen" @close="manageOpen = false" />
  </div>
</template>
