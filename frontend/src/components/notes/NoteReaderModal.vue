<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import MarkdownIt from 'markdown-it'
import taskLists from 'markdown-it-task-lists'
import hljs from 'highlight.js/lib/core'
import 'highlight.js/styles/github.css'
import bash from 'highlight.js/lib/languages/bash'
import css from 'highlight.js/lib/languages/css'
import dockerfile from 'highlight.js/lib/languages/dockerfile'
import javascript from 'highlight.js/lib/languages/javascript'
import json from 'highlight.js/lib/languages/json'
import markdown from 'highlight.js/lib/languages/markdown'
import powershell from 'highlight.js/lib/languages/powershell'
import python from 'highlight.js/lib/languages/python'
import scss from 'highlight.js/lib/languages/scss'
import sql from 'highlight.js/lib/languages/sql'
import typescript from 'highlight.js/lib/languages/typescript'
import xml from 'highlight.js/lib/languages/xml'
import yaml from 'highlight.js/lib/languages/yaml'

import BaseModal from '../BaseModal.vue'
import { useNotesStore } from '../../stores/notes'
import { fmtDate } from '../../utils/date'

hljs.registerLanguage('bash', bash)
hljs.registerLanguage('css', css)
hljs.registerLanguage('dockerfile', dockerfile)
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('json', json)
hljs.registerLanguage('markdown', markdown)
hljs.registerLanguage('powershell', powershell)
hljs.registerLanguage('python', python)
hljs.registerLanguage('scss', scss)
hljs.registerLanguage('sql', sql)
hljs.registerLanguage('typescript', typescript)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('yaml', yaml)
// highlight.js 没有内置 vue，映射到 xml（HTML/组件）高亮
hljs.registerAliases(['vue'], { languageName: 'xml' })

const props = defineProps({
  note: { type: Object, default: null }
})
const emit = defineEmits(['close'])

const notesStore = useNotesStore()
const current = ref(props.note)
watch(
  () => props.note,
  (n) => {
    current.value = n
  }
)

const siblings = computed(() =>
  notesStore.notes.filter((n) => n.folder === current.value?.folder)
)

// 给代码块每行加行号：把高亮后的 HTML 按行拆分，用 CSS 计数器在左侧显示序号（与 Typora 一致）。
function withLineNumbers(codeHtml) {
  return codeHtml
    .replace(/\n$/, '') // 去掉结尾换行，避免多出一个空行号
    .split('\n')
    .map((line) => `<span class="code-line">${line || ' '}</span>`)
    .join('')
}

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight(str, lang) {
    let code
    if (lang && hljs.getLanguage(lang)) {
      try {
        code = hljs.highlight(str, { language: lang, ignoreIllegals: true }).value
      } catch {
        code = md.utils.escapeHtml(str)
      }
    } else {
      code = md.utils.escapeHtml(str)
    }
    return '<pre class="line-numbers"><code class="hljs">' + withLineNumbers(code) + '</code></pre>'
  }
})
md.use(taskLists)

// md 里相邻的 `>` 引用行之间常有空行，会被 markdown-it 拆成多个独立的 <blockquote>，
// 视觉上就成了断开的几块。这里把相邻的引用块合并成一整块，像 Typora 一样左边框连续。
function mergeConsecutiveBlockquotes(html) {
  return html.replace(/<\/blockquote>\s*<blockquote>/g, '')
}
const renderedHtml = computed(() => {
  const content = String(current.value?.content || '').replace(/\r\n/g, '\n').replace(/\r/g, '')
  return mergeConsecutiveBlockquotes(md.render(content))
})

/* ---------- 侧栏状态 ---------- */
const activeTab = ref('outline')
const sidebarCollapsed = ref(false)

/* ---------- 大纲 ---------- */
const bodyEl = ref(null)
const outlineRoot = ref(null)
const nodeCollapsed = ref({})

function slugify(text) {
  const slug = (text || '')
    .trim()
    .toLowerCase()
    .replace(/[^\w\u4e00-\u9fa5]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return slug || 'section'
}

function buildOutline() {
  const rootEl = bodyEl.value
  if (!rootEl) return

  // 收集全部正文标题（h1~h6），先按原始级别生成大纲，再统一降级正文 h1
  const headingEls = [...rootEl.querySelectorAll('h1:not(.note-title), h2, h3, h4, h5, h6')]
  const seen = new Set(['note-title'])
  headingEls.forEach((h) => {
    const base = slugify(h.textContent)
    let id = base
    let i = 2
    while (seen.has(id)) id = `${base}-${i++}`
    seen.add(id)
    h.id = id
  })

  // 用栈按标题级别构筑层级树：h1 为顶层，h2 归属当前 h1，h3 归属当前 h2，依此类推
  // 根节点为虚拟容器（不渲染正文文件名），大纲只包含正文里实际写出的标题。
  const root = { id: '__root__', text: '', children: [] }
  const stack = [{ node: root, level: 0 }]
  headingEls.forEach((h) => {
    const level = Number(h.tagName[1]) // 'H1' -> 1 ... 'H6' -> 6
    const item = { id: h.id, text: h.textContent.trim(), children: [], level }
    while (stack.length > 1 && stack[stack.length - 1].level >= level) stack.pop()
    stack[stack.length - 1].node.children.push(item)
    stack.push({ node: item, level })
  })
  outlineRoot.value = root

  // 默认只展开前两级（h1 书名/章节、h2 小节），更深层（h3+）收起，像 Typora 大纲一样简洁
  const collapsed = {}
  const markCollapsed = (node) => {
    if (node.level >= 2) collapsed[node.id] = true
    node.children.forEach(markCollapsed)
  }
  markCollapsed(root)
  nodeCollapsed.value = collapsed

  // 正文 h1（章节）降级为 h2，与 note-title 区分；保留 id 以便大纲跳转
  rootEl.querySelectorAll('h1:not(.note-title)').forEach((h1) => {
    const h2 = document.createElement('h2')
    h2.id = h1.id
    h2.innerHTML = h1.innerHTML
    h1.replaceWith(h2)
  })
}

watch(
  [renderedHtml, current],
  async () => {
    await nextTick()
    buildOutline()
  },
  { immediate: true }
)

function toggleNode(id) {
  nodeCollapsed.value = { ...nodeCollapsed.value, [id]: !nodeCollapsed.value[id] }
}

function olClass(level) {
  if (level <= 1) return 'h1'
  if (level === 2) return 'h2'
  return 'h3'
}

const outlineItems = computed(() => {
  const items = []
  const walk = (node) => {
    const collapsed = !!nodeCollapsed.value[node.id]
    items.push({
      id: node.id,
      text: node.text,
      level: node.level,
      hasChildren: node.children.length > 0,
      collapsed
    })
    if (!collapsed) node.children.forEach(walk)
  }
  outlineRoot.value?.children.forEach(walk)
  return items
})

function jumpTo(id) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function switchNote(note) {
  current.value = note
}
</script>

<template>
  <BaseModal @close="emit('close')">
    <div class="reader-modal" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
      <div class="reader-main">
        <aside class="reader-side">
          <div class="side-tabs">
            <button
              class="side-tab"
              :class="{ active: activeTab === 'outline' }"
              @click="activeTab = 'outline'"
            >
              大纲
            </button>
            <button
              class="side-tab"
              :class="{ active: activeTab === 'files' }"
              @click="activeTab = 'files'"
            >
              文件
            </button>
          </div>
          <nav v-if="activeTab === 'outline' && outlineRoot" class="outline-tree">
            <div
              v-for="item in outlineItems"
              :key="item.id"
              class="ol-node"
              :class="{ collapsed: item.collapsed }"
            >
              <div class="ol-row" :style="{ paddingLeft: (item.level - 1) * 14 + 'px' }">
                <button v-if="item.hasChildren" class="ol-chev" title="展开/收起" @click="toggleNode(item.id)">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12">
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </button>
                <span v-else class="ol-chev empty"></span>
                <button class="ol-item" :class="olClass(item.level)" @click="jumpTo(item.id)">
                  {{ item.text }}
                </button>
              </div>
            </div>
          </nav>
          <div v-else class="file-panel">
            <div class="file-caption">{{ current?.folder }}</div>
            <button
              v-for="n in siblings"
              :key="n.id"
              class="file-item"
              :class="{ active: n.id === current?.id }"
              @click="switchNote(n)"
            >
              {{ n.title }}
            </button>
          </div>
        </aside>

        <div ref="bodyEl" class="reader-body markdown-body">
          <h1 id="note-title" class="note-title">{{ current?.title || '无标题' }}</h1>
          <p class="meta-line">
            {{ current?.folder }} / {{ fmtDate(current?.updated_at) }}
            <template v-for="t in current?.tags || []" :key="t"> #{{ t }}</template>
          </p>
          <div v-if="renderedHtml" v-html="renderedHtml"></div>
          <p v-else class="empty-tip">暂无内容</p>
        </div>

        <button
          class="sidebar-toggle"
          title="展示/隐藏侧边栏"
          @click="sidebarCollapsed = !sidebarCollapsed"
        >
          <span class="st-icon">‹</span>
          <span class="st-label">展示/隐藏侧边栏</span>
        </button>
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
  /* Github 阅读主题局部令牌（组件内使用，不进入全局主题） */
  --gh-canvas: #fff;
  --gh-ink: #24292e;
  --gh-strong: #1f2328;
  --gh-muted: #57606a;
  --gh-muted-2: #6a737d;
  --gh-border: #eaecef;
  --gh-border-strong: #d0d7de;
  --gh-blockquote: #dfe2e5;
  --gh-hr: #e1e4e8;
  --gh-hover: #f6f8fa;
  --gh-chev: #8c959f;
  --gh-toggle-hover: #eceef0;
  --gh-scrollbar: #b6bcc4;
  --gh-link: #0366d6;
  --gh-code-inline: rgba(27, 31, 35, 0.06);
  --gh-shadow-lg: rgba(0, 0, 0, 0.24);
  --gh-shadow-sm: rgba(0, 0, 0, 0.12);
  position: relative;
  width: min(1440px, 100%);
  height: min(94vh, 980px);
  background: var(--gh-canvas);
  border-radius: 12px;
  box-shadow: 0 18px 50px var(--gh-shadow-lg);
  overflow: hidden;
  color: var(--gh-ink);
  font-family: var(--sans);
  -webkit-font-smoothing: antialiased;
}
.reader-main {
  position: relative;
  display: flex;
  min-height: 0;
  height: 100%;
}

/* ---------- 侧栏 ---------- */
.reader-side {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  padding: 10px 8px 12px;
  border-right: 1px solid var(--gh-border);
  overflow: hidden;
  font-family: var(--sans);
  transition: width 0.3s ease, padding 0.3s ease, border-right-color 0.3s ease;
}
.side-tabs {
  display: flex;
  gap: 2px;
  padding: 4px 4px 0;
  flex-shrink: 0;
  border-bottom: 1px solid var(--gh-border);
}
.side-tab {
  flex: 1;
  padding: 7px 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--gh-muted);
  border-bottom: 2px solid transparent;
  border-radius: 6px 6px 0 0;
  cursor: pointer;
}
.side-tab:hover {
  background: var(--gh-hover);
  color: var(--gh-strong);
}
.side-tab.active {
  color: var(--gh-strong);
  border-bottom-color: var(--gh-strong);
}
.outline-tree {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 10px 6px 12px 4px;
}
.file-panel {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 8px 4px 12px;
}
.file-caption {
  padding: 2px 10px 6px;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--gh-muted-2);
}
.file-item {
  display: block;
  width: 100%;
  padding: 8px 10px;
  text-align: left;
  border-radius: 6px;
  font-size: 13px;
  color: var(--gh-ink);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-item:hover {
  background: var(--gh-hover);
}
.file-item.active {
  background: var(--gh-hover);
  color: var(--gh-link);
  font-weight: 600;
}
.ol-row {
  display: flex;
  align-items: center;
}
.ol-chev {
  display: grid;
  place-items: center;
  width: 20px;
  height: 24px;
  flex-shrink: 0;
  border-radius: 5px;
  color: var(--gh-chev);
  cursor: pointer;
}
.ol-chev:hover {
  color: var(--gh-strong);
  background: var(--gh-hover);
}
.ol-chev.empty {
  pointer-events: none;
}
.ol-chev svg {
  transition: transform 0.18s ease;
}
.ol-node.collapsed > .ol-row .ol-chev svg {
  transform: rotate(-90deg);
}
.ol-item {
  flex: 1;
  min-width: 0;
  padding: 5px 10px;
  border-radius: 6px;
  font-family: var(--sans);
  font-size: 14px;
  font-weight: 400;
  line-height: 1.45;
  color: var(--gh-muted);
  text-align: left;
  cursor: pointer;
}
.ol-row:hover .ol-item {
  background: var(--gh-hover);
  color: var(--gh-strong);
}
.ol-item.h1 {
  font-weight: 700;
  color: var(--gh-strong);
}
.ol-item.h2 {
  font-size: 13px;
  color: var(--gh-muted);
}
.ol-item.h3 {
  font-size: 13px;
  color: var(--gh-muted-2);
}

/* ---------- 侧栏开关 ---------- */
.sidebar-toggle {
  position: absolute;
  left: calc(240px - 13px);
  bottom: 16px;
  z-index: 20;
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1px solid var(--gh-border-strong);
  background: var(--gh-canvas);
  color: var(--gh-muted);
  box-shadow: 0 1px 4px var(--gh-shadow-sm);
  cursor: pointer;
  transition: left 0.3s ease;
}
.sidebar-toggle::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: var(--gh-toggle-hover);
  opacity: 0;
  transition: opacity 0.18s ease;
}
.sidebar-toggle:hover::before {
  opacity: 1;
}
.sidebar-toggle:hover .st-icon {
  color: var(--gh-strong);
}
.sidebar-toggle .st-icon {
  position: relative;
  z-index: 1;
  font-size: 18px;
  line-height: 1;
  transition: transform 0.3s ease;
}
.st-label {
  position: absolute;
  left: calc(100% + 10px);
  top: 50%;
  transform: translateY(-50%);
  white-space: nowrap;
  padding: 4px 10px;
  border-radius: 6px;
  background: var(--gh-strong);
  color: var(--gh-canvas);
  font-size: 12px;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.18s ease;
}
.sidebar-toggle:hover .st-label {
  opacity: 1;
}
.reader-modal.sidebar-collapsed .sidebar-toggle {
  left: 14px;
}
.reader-modal.sidebar-collapsed .sidebar-toggle .st-icon {
  transform: rotate(180deg);
}

/* ---------- 收起态 ---------- */
.reader-modal.sidebar-collapsed .reader-side {
  width: 0;
  padding-left: 0;
  padding-right: 0;
  border-right-color: transparent;
}
.reader-modal.sidebar-collapsed .reader-body {
  max-width: 1200px;
  margin: 0 auto;
  padding: 8px 56px 110px;
}

/* ---------- 正文 ---------- */
.reader-body {
  flex: 1;
  min-width: 0;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 44px 64px;
  transition: padding 0.3s ease;
}
.reader-close {
  position: absolute;
  top: 12px;
  right: 28px;
  z-index: 30;
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid var(--gh-border-strong);
  background: var(--gh-canvas);
  color: var(--gh-muted);
  box-shadow: 0 1px 4px var(--gh-shadow-sm);
  cursor: pointer;
}
.reader-close:hover {
  border-color: var(--gh-link);
  color: var(--gh-link);
}

/* ---------- Typora Github 主题正文 ---------- */
.markdown-body {
  color: var(--gh-ink);
  font-size: 16px;
  line-height: 1.75;
  overflow-wrap: break-word;
}
.markdown-body :deep(.note-title) {
  margin: 0 0 6px;
  padding-bottom: 0.3em;
  border-bottom: 1px solid var(--gh-border);
  font-size: 1.9em;
  font-weight: 600;
  line-height: 1.3;
}
.markdown-body :deep(.meta-line) {
  margin: 6px 0 0;
  color: var(--gh-muted-2);
  font-size: 13px;
}
.markdown-body :deep(.empty-tip) {
  margin: 1em 0;
  color: var(--gh-muted-2);
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
  border-bottom: 1px solid var(--gh-border);
}
.markdown-body :deep(h2) {
  font-size: 1.5em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid var(--gh-border);
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
  color: var(--gh-link);
  text-decoration: none;
  overflow-wrap: anywhere;
}
.markdown-body :deep(a:hover) {
  text-decoration: underline;
}
.markdown-body :deep(blockquote) {
  margin: 0.9em 0;
  padding: 0.3em 1em;
  border-left: 4px solid var(--gh-blockquote);
  color: var(--gh-muted-2);
}
.markdown-body :deep(blockquote p) {
  margin: 0.3em 0;
}
.markdown-body :deep(code) {
  padding: 0.15em 0.4em;
  border-radius: 6px;
  background: var(--gh-code-inline);
  font-family: var(--mono, 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace);
  font-size: 0.88em;
}
.markdown-body :deep(pre) {
  margin: 0.9em 0;
  padding: 14px 16px;
  background: var(--gh-hover);
  border: 1px solid var(--gh-border);
  border-radius: 8px;
  overflow: auto;
}
.markdown-body :deep(pre code) {
  padding: 0;
  background: transparent;
  font-size: 13.5px;
  line-height: 1.6;
}
.markdown-body :deep(pre.line-numbers) {
  counter-reset: line;
}
.markdown-body :deep(pre.line-numbers code) {
  display: block;
}
.markdown-body :deep(pre.line-numbers .code-line) {
  display: block;
}
.markdown-body :deep(pre.line-numbers .code-line::before) {
  counter-increment: line;
  content: counter(line);
  display: inline-block;
  width: 2em;
  margin-right: 1em;
  text-align: right;
  color: var(--gh-muted-2);
  user-select: none;
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
  border: 1px solid var(--gh-border-strong);
  text-align: left;
}
.markdown-body :deep(th) {
  background: var(--gh-hover);
  font-weight: 600;
}
.markdown-body :deep(hr) {
  margin: 1.6em 0;
  border: 0;
  border-top: 1px solid var(--gh-hr);
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
.markdown-body :deep(li.task-list-item:has(input:checked)) {
  color: var(--gh-muted-2);
  text-decoration: line-through;
}
.reader-body::-webkit-scrollbar,
.outline-tree::-webkit-scrollbar,
.file-panel::-webkit-scrollbar {
  width: 8px;
}
.reader-body::-webkit-scrollbar-track,
.outline-tree::-webkit-scrollbar-track,
.file-panel::-webkit-scrollbar-track {
  background: transparent;
}
.reader-body::-webkit-scrollbar-thumb,
.outline-tree::-webkit-scrollbar-thumb,
.file-panel::-webkit-scrollbar-thumb {
  background: var(--gh-border-strong);
  border-radius: 999px;
}
.reader-body::-webkit-scrollbar-thumb:hover,
.outline-tree::-webkit-scrollbar-thumb:hover,
.file-panel::-webkit-scrollbar-thumb:hover {
  background: var(--gh-scrollbar);
}
</style>
