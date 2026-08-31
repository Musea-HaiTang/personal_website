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

/**
 * 渲染 markdown 笔记正文，返回渲染后的 HTML。
 * @param {string} content 原始 markdown 文本
 * @returns {{ html: string }}
 */
export function renderNote(content) {
  const text = String(content || '').replace(/\r\n/g, '\n').replace(/\r/g, '')
  return { html: mergeConsecutiveBlockquotes(md.render(text)) }
}
