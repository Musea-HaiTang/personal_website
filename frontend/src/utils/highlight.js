export function escHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
}

/** 转义后高亮关键词（返回带 <mark> 的 HTML，仅用于 v-html）。 */
export function hlHtml(text, keyword = '') {
  const esc = escHtml(text)
  const kw = (keyword || '').trim()
  if (!kw) return esc
  const idx = esc.toLowerCase().indexOf(kw.toLowerCase())
  if (idx === -1) return esc
  return (
    esc.slice(0, idx) +
    '<mark class="rounded bg-amber-soft px-0.5 text-amber-dark">' +
    esc.slice(idx, idx + kw.length) +
    '</mark>' +
    esc.slice(idx + kw.length)
  )
}
