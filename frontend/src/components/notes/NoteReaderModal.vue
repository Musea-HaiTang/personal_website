<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

import BaseModal from '../BaseModal.vue'
import { useNotesStore } from '../../stores/notes'
import { fmtDate } from '../../utils/date'

const props = defineProps({
  note: { type: Object, default: null }
})
const emit = defineEmits(['close', 'removed'])

const notesStore = useNotesStore()
const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

const renderedHtml = computed(() => md.render(props.note?.content || ''))

async function remove() {
  if (!props.note || !window.confirm('确定删除这篇笔记？正文文件也会被删除。')) return
  try {
    await notesStore.remove(props.note.id)
    emit('removed')
  } catch (e) {
    window.alert(e.response?.data?.detail || '删除失败')
  }
}
</script>

<template>
  <BaseModal @close="emit('close')">
    <div class="letter flex max-h-[90vh] w-full max-w-5xl flex-col overflow-hidden">
      <div class="flex items-start gap-4">
        <h2 class="min-w-0 flex-1 font-serif text-2xl font-bold leading-snug text-ink">
          {{ note?.title || '无标题' }}
        </h2>
        <div class="flex shrink-0 gap-1.5">
          <button class="rounded-lg p-1.5 text-sub hover:bg-red-soft hover:text-red" title="删除" @click="remove">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="h-4 w-4">
              <path d="M4 7h16M9 7V5h6v2M6 7l1 13h10l1-13M10 11v5M14 11v5" />
            </svg>
          </button>
          <button class="rounded-lg p-1.5 text-sub hover:bg-teal-soft hover:text-teal" title="关闭" @click="emit('close')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="h-4 w-4">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </div>
      </div>
      <div class="mt-2 flex flex-wrap items-center gap-2 border-b border-hairline pb-3 text-xs text-sub">
        <span>{{ note?.folder }} · {{ fmtDate(note?.updated_at) }}</span>
        <span
          v-for="t in note?.tags || []"
          :key="t"
          class="rounded-full bg-teal-soft px-2.5 py-px text-teal-dark"
        >
          {{ t }}
        </span>
      </div>
      <div class="article-scroll mt-4 min-h-0 flex-1 overflow-y-auto">
        <div v-if="renderedHtml" v-html="renderedHtml" class="markdown-body"></div>
        <p v-else class="text-sm text-sub">暂无内容</p>
      </div>
    </div>
  </BaseModal>
</template>

<style scoped>
.letter {
  background: #fffefc;
  border: 1px solid #ddd8cf;
  border-radius: 10px;
  box-shadow: 0 16px 40px rgba(43, 38, 34, 0.18);
  padding: 30px 36px;
}
.article-scroll {
  padding-right: 4px;
}
.markdown-body {
  color: var(--ink);
  font-size: 16px;
  line-height: 1.9;
  overflow-wrap: break-word;
}
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  font-family: var(--serif);
  line-height: 1.35;
  margin: 1.2em 0 0.5em;
}
.markdown-body :deep(h1) {
  font-size: 1.7em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid var(--hairline);
}
.markdown-body :deep(h2) {
  font-size: 1.35em;
  padding-bottom: 0.25em;
  border-bottom: 1px solid var(--hairline);
}
.markdown-body :deep(h3) {
  font-size: 1.15em;
}
.markdown-body :deep(p) {
  margin: 0.7em 0;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.7em 0;
  padding-left: 1.5em;
}
.markdown-body :deep(li) {
  margin: 0.25em 0;
}
.markdown-body :deep(a) {
  color: var(--teal);
  text-decoration: underline;
  overflow-wrap: anywhere;
}
.markdown-body :deep(blockquote) {
  margin: 0.8em 0;
  padding: 0.1em 1em;
  border-left: 3px solid var(--teal);
  color: var(--sub);
  background: var(--teal-soft);
  border-radius: 0 8px 8px 0;
}
.markdown-body :deep(code) {
  padding: 0.15em 0.4em;
  border-radius: 5px;
  background: var(--teal-soft);
  color: var(--teal-dark);
  font-size: 0.9em;
}
.markdown-body :deep(pre) {
  margin: 0.9em 0;
  padding: 14px 16px;
  overflow-x: auto;
  border-radius: 8px;
  background: #f2eee7;
  border: 1px solid var(--hairline);
}
.markdown-body :deep(pre code) {
  padding: 0;
  background: transparent;
  color: var(--ink);
}
.markdown-body :deep(table) {
  width: 100%;
  margin: 0.9em 0;
  border-collapse: collapse;
  font-size: 0.95em;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 7px 10px;
  border: 1px solid var(--hairline);
  text-align: left;
}
.markdown-body :deep(th) {
  background: var(--paper-soft);
  font-weight: 600;
}
.markdown-body :deep(hr) {
  margin: 1.4em 0;
  border: 0;
  border-top: 1px solid var(--hairline);
}
.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 8px;
}
.letter ::-webkit-scrollbar {
  width: 6px;
}
.letter ::-webkit-scrollbar-track {
  background: transparent;
}
.letter ::-webkit-scrollbar-thumb {
  background: var(--ink);
  border-radius: 999px;
}
</style>
