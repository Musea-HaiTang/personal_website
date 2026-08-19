<script setup>
import { computed } from 'vue'
import MarkdownIt from 'markdown-it'

import BaseModal from '../BaseModal.vue'
import { fmtDate } from '../../utils/date'

const props = defineProps({
  note: { type: Object, default: null }
})
const emit = defineEmits(['close'])

const md = new MarkdownIt({ html: false, linkify: true, breaks: true })

const renderedHtml = computed(() => md.render(props.note?.content || ''))
</script>

<template>
  <BaseModal @close="emit('close')">
    <div class="reader-modal">
      <div class="reader-body markdown-body">
        <h1 class="note-title">{{ note?.title || '无标题' }}</h1>
        <p class="meta-line">
          {{ note?.folder }} / {{ fmtDate(note?.updated_at) }}
          <template v-for="t in note?.tags || []" :key="t"> #{{ t }}</template>
        </p>
        <div v-if="renderedHtml" v-html="renderedHtml"></div>
        <p v-else class="empty-tip">暂无内容</p>
      </div>
      <button class="reader-close" title="关闭" @click="emit('close')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" width="15" height="15">
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      </button>
    </div>
  </BaseModal>
</template>

<style scoped>
.reader-modal {
  position: relative;
  display: flex;
  flex-direction: column;
  width: min(1440px, 100%);
  height: min(94vh, 980px);
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.24);
  overflow: hidden;
  color: #24292e;
  font-family: var(--sans);
  -webkit-font-smoothing: antialiased;
}
.reader-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 44px 64px;
}
.reader-close {
  position: absolute;
  top: 12px;
  right: 28px;
  z-index: 10;
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid #d0d7de;
  background: #fff;
  color: #57606a;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.14);
  cursor: pointer;
}
.reader-close:hover {
  border-color: #0366d6;
  color: #0366d6;
}

/* ---------- Typora Github 主题正文 ---------- */
.markdown-body {
  color: #24292e;
  font-size: 16px;
  line-height: 1.75;
  overflow-wrap: break-word;
}
.markdown-body :deep(.note-title) {
  margin: 0 0 6px;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #eaecef;
  font-size: 1.9em;
  font-weight: 600;
  line-height: 1.3;
}
.markdown-body :deep(.meta-line) {
  margin: 6px 0 0;
  color: #6a737d;
  font-size: 13px;
}
.markdown-body :deep(.empty-tip) {
  margin: 1em 0;
  color: #6a737d;
  font-size: 14px;
}
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  font-weight: 600;
  line-height: 1.3;
  margin: 1.4em 0 0.6em;
}
.markdown-body :deep(h1) {
  font-size: 1.9em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #eaecef;
}
.markdown-body :deep(h2) {
  font-size: 1.5em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid #eaecef;
}
.markdown-body :deep(h3) {
  font-size: 1.25em;
}
.markdown-body :deep(h4) {
  font-size: 1em;
}
.markdown-body :deep(p) {
  margin: 0.7em 0;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0.7em 0;
  padding-left: 1.6em;
}
.markdown-body :deep(li) {
  margin: 0.25em 0;
}
.markdown-body :deep(a) {
  color: #0366d6;
  text-decoration: none;
  overflow-wrap: anywhere;
}
.markdown-body :deep(a:hover) {
  text-decoration: underline;
}
.markdown-body :deep(blockquote) {
  margin: 0.9em 0;
  padding: 0.15em 1em;
  border-left: 4px solid #dfe2e5;
  color: #6a737d;
}
.markdown-body :deep(code) {
  padding: 0.15em 0.4em;
  border-radius: 6px;
  background: rgba(27, 31, 35, 0.06);
  font-family: var(--mono, 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace);
  font-size: 0.88em;
}
.markdown-body :deep(pre) {
  margin: 0.9em 0;
  padding: 14px 16px;
  background: #f6f8fa;
  border: 1px solid #eaecef;
  border-radius: 8px;
  overflow: auto;
}
.markdown-body :deep(pre code) {
  padding: 0;
  background: transparent;
  font-size: 13.5px;
  line-height: 1.6;
}
.markdown-body :deep(table) {
  width: 100%;
  margin: 0.9em 0;
  border-collapse: collapse;
  font-size: 0.95em;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
  padding: 7px 12px;
  border: 1px solid #d0d7de;
  text-align: left;
}
.markdown-body :deep(th) {
  background: #f6f8fa;
  font-weight: 600;
}
.markdown-body :deep(hr) {
  margin: 1.6em 0;
  border: 0;
  border-top: 1px solid #e1e4e8;
}
.markdown-body :deep(img) {
  max-width: 100%;
  border-radius: 8px;
}
.markdown-body :deep(.task-list-item) {
  list-style: none;
  margin-left: -1.4em;
}
.markdown-body :deep(.task-list-item input) {
  margin-right: 0.45em;
  transform: translateY(1px);
}
.markdown-body :deep(.task-done) {
  color: #6a737d;
  text-decoration: line-through;
}
.reader-body::-webkit-scrollbar {
  width: 8px;
}
.reader-body::-webkit-scrollbar-track {
  background: transparent;
}
.reader-body::-webkit-scrollbar-thumb {
  background: #d0d7de;
  border-radius: 999px;
}
.reader-body::-webkit-scrollbar-thumb:hover {
  background: #b6bcc4;
}
</style>
