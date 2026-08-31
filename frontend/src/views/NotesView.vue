<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import ImportNotesModal from '../components/notes/ImportNotesModal.vue'
import NoteReaderModal from '../components/notes/NoteReaderModal.vue'
import { useNotesStore } from '../stores/notes'
import { fmtDate } from '../utils/date'
import { hlHtml } from '../utils/highlight'

const notesStore = useNotesStore()

/* ---------- 笔记列表 ---------- */
const chips = computed(() => [
  { folder: 'all', name: '全部', count: notesStore.total },
  ...notesStore.folders.map((f) => ({ folder: f.folder, name: f.folder, count: f.count }))
])

/* ---------- 弹窗编排 ---------- */
const readerNote = ref(null)
const importOpen = ref(false)

const readerOpen = computed(() => readerNote.value !== null)
const importNotice = ref('')
let importNoticeTimer = null

async function openReader(note) {
  try {
    readerNote.value = await notesStore.fetchNote(note.id)
  } catch (e) {
    window.alert(e.response?.data?.detail || '打开笔记失败')
  }
}
function closeReader() {
  readerNote.value = null
}
function showImportNotice(message) {
  importNotice.value = message
  if (importNoticeTimer) window.clearTimeout(importNoticeTimer)
  importNoticeTimer = window.setTimeout(() => {
    importNotice.value = ''
  }, 5000)
}
async function onImported(message = '') {
  importOpen.value = false
  showImportNotice(message)
  await notesStore.refresh()
}
async function removeNote(note) {
  if (!window.confirm(`删除《${note.title}》？正文文件也会被删除。`)) return
  try {
    await notesStore.remove(note.id)
    await notesStore.refresh()
  } catch (e) {
    window.alert(e.response?.data?.detail || '删除失败')
  }
}
let kwTimer = null
watch(
  () => notesStore.kw,
  () => {
    if (kwTimer) window.clearTimeout(kwTimer)
    kwTimer = window.setTimeout(() => notesStore.refresh(), 300)
  }
)
onMounted(() => {
  if (!notesStore.loaded) notesStore.refresh()
})
onBeforeUnmount(() => {
  if (importNoticeTimer) window.clearTimeout(importNoticeTimer)
  if (kwTimer) window.clearTimeout(kwTimer)
})
</script>

<template>
  <div class="flex h-full flex-col gap-4">
    <div>
      <h1 class="font-serif text-2xl tracking-wide text-ink">笔记</h1>
    </div>

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

    <div
      v-if="importNotice"
      class="rounded-lg border border-teal bg-teal-soft px-4 py-2.5 text-sm text-teal-dark"
    >
      {{ importNotice }}
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
      <div v-for="n in notesStore.filtered" :key="n.id" class="relative">
        <button
          class="flex w-full flex-col gap-1.5 rounded-xl border border-hairline bg-card p-4 pr-9 text-left hover:border-teal"
          @click="openReader(n)"
        >
          <span class="font-medium text-ink" v-html="hlHtml(n.title, notesStore.kw)"></span>
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
        <button
          class="absolute right-2 top-2 rounded-lg p-1.5 text-sub hover:bg-red-soft hover:text-red"
          title="删除"
          @click="removeNote(n)"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="h-4 w-4">
            <path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13M10 11v5M14 11v5" />
          </svg>
        </button>
      </div>
    </div>

    <!-- 弹窗 -->
    <NoteReaderModal
      v-if="readerOpen"
      :note="readerNote"
      @close="closeReader"
    />
    <ImportNotesModal v-if="importOpen" @close="importOpen = false" @imported="onImported" />
  </div>
</template>
