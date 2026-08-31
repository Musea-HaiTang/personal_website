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

function slugify(text) {
  const slug = (text || '')
    .trim()
    .toLowerCase()
    .replace(/[^\w\u4e00-\u9fa5]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return slug || 'section'
}

// 从标题的 inline token 提取可读纯文本（近似 DOM textContent，忽略图片 alt）。
function headingText(inlineToken) {
  if (!inlineToken) return ''
  const parts = []
  for (const c of inlineToken.children || []) {
    if (c.type === 'text' || c.type === 'code_inline') parts.push(c.content)
  }
  return parts.join('').trim()
}

/**
 * 渲染 markdown 笔记正文，返回渲染后的 HTML 与从解析树提取的标题列表。
 * @param {string} content 原始 markdown 文本
 * @returns {{ html: string, headings: Array<{id: string, level: number, text: string}> }}
 */
export function renderNote(content) {
  const text = String(content || '').replace(/\r\n/g, '\n').replace(/\r/g, '')
  const tokens = md.parse(text, {})
  const seen = new Set(['note-title']) // note-title 是文档标题，占据固定 id
  const headings = []

  for (let i = 0; i < tokens.length; i++) {
    const t = tokens[i]
    if (t.type !== 'heading_open') continue
    const level = Number(t.tag[1]) // 'h1' -> 1 ... 'h6' -> 6
    const textPlain = headingText(tokens[i + 1])
    const base = slugify(textPlain)
    let id = base
    let n = 2
    while (seen.has(id)) id = `${base}-${n++}`
    seen.add(id)
    t.attrSet('id', id)
    headings.push({ id, level, text: textPlain })

    // 内容 h1（章节）降级为 h2，与标题区 note-title 区分；大纲仍按作者结构用原始级别。
    if (level === 1) {
      t.tag = 'h2'
      const close = tokens[i + 2]
      if (close && close.type === 'heading_close') close.tag = 'h2'
    }
  }

  const html = mergeConsecutiveBlockquotes(md.renderer.render(tokens, md.options, {}))
  return { html, headings }
}
