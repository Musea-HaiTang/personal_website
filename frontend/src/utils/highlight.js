export function escHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
}

/** 转义后高亮关键词（返回带 <mark> 的 HTML，仅用于 v-html）；markClass 可覆盖高亮样式。 */
export function hlHtml(text, keyword = '', markClass = 'rounded bg-amber-soft px-0.5 text-amber-dark') {
  const esc = escHtml(text)
  const kw = (keyword || '').trim()
  if (!kw) return esc
  const idx = esc.toLowerCase().indexOf(kw.toLowerCase())
  if (idx === -1) return esc
  return (
    esc.slice(0, idx) +
    `<mark class="${markClass}">` +
    esc.slice(idx, idx + kw.length) +
    '</mark>' +
    esc.slice(idx + kw.length)
  )
}
