<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import BaseModal from '../BaseModal.vue'
import { useNotesStore } from '../../stores/notes'
import { fmtDate } from '../../utils/date'

const props = defineProps({
  note: { type: Object, default: null }
})
const emit = defineEmits(['close', 'saved', 'removed', 'dirty-change'])

const notesStore = useNotesStore()

const editTitle = ref('')
const editTags = ref([])
const editContent = ref('')
const dirty = ref(false)
const savedMsg = ref('')
const tagInputOpen = ref(false)
const newTag = ref('')
const saving = ref(false)

watch(
  () => props.note,
  (note) => {
    if (!note) return
    editTitle.value = note.title
    editTags.value = [...(note.tags || [])]
    editContent.value = note.content || ''
    dirty.value = false
    savedMsg.value = ''
    tagInputOpen.value = false
  },
  { immediate: true }
)

function markDirty() {
  dirty.value = true
  savedMsg.value = ''
  emit('dirty-change', true)
}
function close() {
  if (dirty.value && !window.confirm('有未保存的修改，确定关闭？修改将丢失。')) return
  emit('dirty-change', false)
  emit('close')
}
async function save() {
  if (props.note === null || saving.value) return
  saving.value = true
  try {
    await notesStore.update(props.note.id, {
      title: editTitle.value.trim() || '无标题',
      tags: editTags.value,
      content: editContent.value
    })
    dirty.value = false
    savedMsg.value = '已保存'
    emit('dirty-change', false)
    emit('saved')
  } catch (e) {
    savedMsg.value = e.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}
async function remove() {
  if (props.note === null) return
  if (!window.confirm('确定删除这篇笔记？正文文件也会被删除。')) return
  try {
    await notesStore.remove(props.note.id)
    emit('removed')
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

function onKeydown(e) {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
    e.preventDefault()
    save()
  }
}
onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <BaseModal @close="close">
    <div class="letter flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden">
      <div class="flex items-start gap-3">
        <input
          v-model="editTitle"
          class="flex-1 bg-transparent font-serif text-2xl font-bold text-ink focus:outline-none"
          placeholder="无标题"
          @input="markDirty"
        >
        <div class="flex gap-1.5">
          <button class="rounded-lg p-1.5 text-sub hover:bg-teal-soft hover:text-teal" title="删除" @click="remove">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="h-4 w-4">
              <path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13M10 11v5M14 11v5" />
            </svg>
          </button>
          <button class="rounded-lg p-1.5 text-sub hover:bg-teal-soft hover:text-teal" title="关闭" @click="close">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="h-4 w-4">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </div>
      </div>
      <div class="mt-1 flex items-center gap-2 text-xs text-sub">
        <span>{{ note?.folder }} · {{ fmtDate(note?.updated_at) }}</span>
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
  </BaseModal>
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
.letter ::-webkit-scrollbar {
  width: 6px;
}
.letter ::-webkit-scrollbar-track {
  background: transparent;
}
.letter ::-webkit-scrollbar-thumb {
  background: #2b2622;
  border-radius: 999px;
}
</style>
