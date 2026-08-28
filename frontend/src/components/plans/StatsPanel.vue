<script setup>
import { computed } from 'vue'

const props = defineProps({
  weeks: { type: Array, default: () => [] },
  error: { type: String, default: '' },
})

const label = (ws) => `${parseInt(ws.slice(5, 7), 10)}/${parseInt(ws.slice(8, 10), 10)}`
const lastRate = computed(() => (props.weeks.length ? props.weeks[props.weeks.length - 1].completion_rate : 0))

function line(weeks) {
  if (!weeks.length) return ''
  const W = 780, H = 220, p = { l: 38, r: 14, t: 14, b: 26 }
  const iw = W - p.l - p.r, ih = H - p.t - p.b
  const x = (i) => p.l + iw * (i / (weeks.length - 1))
  const y = (r) => p.t + ih * (1 - r / 100)
  let pts = '', area = `M${x(0)},${y(weeks[0].completion_rate)}`
  weeks.forEach((d, i) => {
    pts += `${x(i)},${y(d.completion_rate)} `
    area += ` L${x(i)},${y(d.completion_rate)}`
  })
  area += ` L${p.l + iw},${p.t + ih} L${p.l},${p.t + ih} Z`
  let grid = ''
  for (let g = 0; g <= 100; g += 25) {
    const gy = y(g)
    grid += `<line x1="${p.l}" y1="${gy}" x2="${p.l + iw}" y2="${gy}" stroke="#eee7dc"/>`
    grid += `<text x="${p.l - 7}" y="${gy + 3}" text-anchor="end" font-size="10" fill="#7c7468">${g}%</text>`
  }
  let dots = '', xl = ''
  weeks.forEach((d, i) => {
    dots += `<circle cx="${x(i)}" cy="${y(d.completion_rate)}" r="3" fill="#0e7c74"/>`
    xl += `<text x="${x(i)}" y="${H - 8}" text-anchor="middle" font-size="9" fill="#7c7468">${label(d.week_start)}</text>`
  })
  return `<svg viewBox="0 0 ${W} ${H}">
    <defs><linearGradient id="pls" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0e7c74" stop-opacity=".18"/><stop offset="1" stop-color="#0e7c74" stop-opacity="0"/>
    </linearGradient></defs>
    ${grid}<path d="${area}" fill="url(#pls)"/>
    <polyline points="${pts}" fill="none" stroke="#0e7c74" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
    ${dots}${xl}</svg>`
}

function bar(weeks) {
  if (!weeks.length) return ''
  const W = 780, H = 220, p = { l: 32, r: 12, t: 14, b: 26 }
  const iw = W - p.l - p.r, ih = H - p.t - p.b
  const group = iw / weeks.length, inner = group * 0.66, bw = inner / 3, gb = Math.max(2, bw * 0.3)
  const max = Math.max(...weeks.map((d) => Math.max(d.plan_count, d.subtask_count, d.task_count)), 1)
  const y = (v) => p.t + ih * (1 - v / max), base = p.t + ih
  const col = { p: '#b7791f', s: '#0e7c74', t: '#b9b0a1' }
  let out = `<svg viewBox="0 0 ${W} ${H}">`
  for (let g = 0; g <= 4; g++) {
    const gy = p.t + ih * (g / 4)
    out += `<line x1="${p.l}" y1="${gy}" x2="${p.l + iw}" y2="${gy}" stroke="#eee7dc"/>`
    out += `<text x="${p.l - 5}" y="${gy + 3}" text-anchor="end" font-size="10" fill="#7c7468">${Math.round(max * (1 - g / 4))}</text>`
  }
  weeks.forEach((d, i) => {
    const gx = p.l + group * i + group / 2
    ;['p', 's', 't'].forEach((k, si) => {
      const bx = gx - inner / 2 + si * (bw + gb), by = y(d[k === 'p' ? 'plan_count' : k === 's' ? 'subtask_count' : 'task_count'])
      out += `<rect x="${bx}" y="${by}" width="${bw}" height="${base - by}" fill="${col[k]}" rx="2"/>`
    })
    out += `<text x="${gx}" y="${H - 8}" text-anchor="middle" font-size="9" fill="#7c7468">${label(d.week_start)}</text>`
  })
  return out + `</svg>`
}

const lineHtml = computed(() => line(props.weeks))
const barHtml = computed(() => bar(props.weeks))
const heatList = computed(() => {
  const items = []
  props.weeks.forEach((d) => {
    for (let day = 0; day < 7; day++) {
      const c = d.daily_counts?.[day]?.count || 0
      items.push({
        cls: c >= 4 ? 'c4' : c >= 3 ? 'c3' : c >= 2 ? 'c2' : c >= 1 ? 'c1' : 'c0',
        title: `${label(d.week_start)} · 周${day + 1} · ${c} 项`,
      })
    }
  })
  return items
})
</script>

<template>
  <div class="stat-grid">
    <p v-if="error" class="mb-4 rounded bg-red-soft px-3 py-2 text-sm text-red">{{ error }}</p>

    <div class="card statcard wide">
      <h3>近 12 周完成率趋势</h3>
      <p class="hint">按周汇总的计划 / 子任务 / 今日任务完成比例</p>
      <div v-html="lineHtml"></div>
      <div class="legend"><span><i style="background:var(--teal)"></i>完成率</span><span>当前 {{ lastRate }}%</span></div>
    </div>

    <div class="card statcard">
      <div class="section"><h3>每周任务数量</h3></div>
      <div v-html="barHtml"></div>
      <div class="legend">
        <span><i style="background:var(--amber)"></i>计划</span>
        <span><i style="background:var(--teal)"></i>子任务</span>
        <span><i style="background:#b9b0a1"></i>今日任务</span>
      </div>
    </div>

    <div class="card statcard">
      <div class="section"><h3>每周完成热力图 · 近 12 周</h3><span class="sub">颜色越深完成越多</span></div>
      <div class="hmwrap">
        <div class="daylab"><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span><span>日</span></div>
        <div class="hmmain">
          <div class="hm">
            <i v-for="(item, idx) in heatList" :key="idx" :class="item.cls" :title="item.title"></i>
          </div>
        </div>
      </div>
      <div class="legend" style="margin-top:12px">
        <span><i style="background:#f4f1ea"></i>0</span>
        <span><i style="background:#cfe6e0"></i>1</span>
        <span><i style="background:#9ccfc4"></i>2</span>
        <span><i style="background:#5fae9f"></i>3</span>
        <span><i style="background:#0e7c74"></i>4</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: 1.35fr 1fr;
  gap: 14px;
}
.stat-grid .wide {
  grid-column: span 2;
}
.card {
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 14px;
  padding: 18px 20px;
}
.statcard h3 {
  font-size: 14px;
  font-weight: 600;
  font-family: var(--serif);
  color: var(--ink);
  margin: 0;
}
.statcard .hint {
  font-size: 11px;
  color: var(--sub);
  margin: 2px 0 0;
}
.section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--hairline);
  padding-bottom: 12px;
  margin-bottom: 12px;
}
.section h3 {
  font-size: 14px;
  font-weight: 600;
  font-family: var(--serif);
  color: var(--ink);
  margin: 0;
}
.sub {
  font-size: 12px;
  color: var(--sub);
}
.legend {
  display: flex;
  gap: 14px;
  align-items: center;
  font-size: 11px;
  color: var(--sub);
  margin-top: 8px;
  flex-wrap: wrap;
}
.legend span {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.legend i {
  width: 10px;
  height: 10px;
  border-radius: 3px;
  display: inline-block;
}
.hmwrap {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.hmmain {
  flex: 1;
}
.hm {
  display: grid;
  grid-template-rows: repeat(7, 13px);
  grid-auto-flow: column;
  grid-auto-columns: 13px;
  gap: 3px;
}
.hm i {
  width: 13px;
  height: 13px;
  border-radius: 3px;
  background: var(--paper-soft);
}
.hm i.c0 { background: var(--paper-soft); }
.hm i.c1 { background: #cfe6e0; }
.hm i.c2 { background: #9ccfc4; }
.hm i.c3 { background: #5fae9f; }
.hm i.c4 { background: var(--teal); }
.daylab {
  display: grid;
  grid-template-rows: repeat(7, 13px);
  gap: 3px;
  font-size: 9px;
  color: var(--sub);
}
.daylab span {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  height: 13px;
  line-height: 13px;
}
@media (max-width: 900px) {
  .stat-grid {
    grid-template-columns: 1fr;
  }
  .stat-grid .wide {
    grid-column: span 1;
  }
}
</style>
