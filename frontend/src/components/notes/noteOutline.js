/**
 * 把文档标题 + 从 markdown 解析树提取的标题列表，构造成大纲树（纯函数，不依赖 DOM）。
 *
 * 结构：根节点为虚拟容器，第一个子节点是文档标题（note-title，层级 1），
 * 其余为正文标题；用栈按标题级别构建层级（h1 为顶层，h2 归属当前 h1，依此类推）。
 *
 * @param {string} title 文档标题（笔记标题，作为大纲顶层）
 * @param {Array<{id: string, level: number, text: string}>} headings 从解析树提取的正文标题
 * @returns {{id: string, text: string, level: number, children: Array}}
 */
export function buildOutlineTree(title, headings) {
  const root = { id: '__root__', text: '', level: 0, children: [] }
  const stack = [{ node: root, level: 0 }]

  const titleItem = { id: 'note-title', text: title || '无标题', level: 1, children: [] }
  root.children.push(titleItem)
  stack.push({ node: titleItem, level: 1 })

  for (const h of headings) {
    const item = { id: h.id, text: h.text, level: h.level, children: [] }
    while (stack.length > 1 && stack[stack.length - 1].level >= h.level) stack.pop()
    stack[stack.length - 1].node.children.push(item)
    stack.push({ node: item, level: h.level })
  }

  return root
}
