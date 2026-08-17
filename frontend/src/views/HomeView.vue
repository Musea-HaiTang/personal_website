<script setup>
import { computed, onMounted, ref } from 'vue'

import { useDashboardStore } from '../stores/dashboard'

const dashboard = useDashboardStore()
const loading = ref(false)
const error = computed(() => dashboard.error)
const iconFailed = ref(new Set())

const impLabels = { 1: '低', 2: '中', 3: '高' }
const impCls = { 1: 'bg-paper-soft text-sub', 2: 'bg-teal-soft text-teal', 3: 'bg-red-soft text-red' }

async function load() {
  loading.value = true
  await dashboard.refresh()
  loading.value = false
}

function formatDuration(totalSeconds) {
  const m = Math.floor(totalSeconds / 60)
  const s = totalSeconds % 60
  if (m >= 60) return `${Math.floor(m / 60)} 小时 ${m % 60} 分钟`
  if (m > 0) return `${m} 分钟${s ? ` ${s} 秒` : ''}`
  return `${s} 秒`
}

function domainOf(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

function faviconUrl(url) {
  return '/api/nav/favicons?domain=' + encodeURIComponent(domainOf(url))
}

function handleIconError(id) {
  iconFailed.value.add(id)
}

function initials(title) {
  return (title || '').trim().slice(0, 1).toUpperCase() || '?'
}

onMounted(load)
</script>

<template>
  <div class="page">
    <header class="page-head">
      <h1>聚合首页</h1>
      <p class="page-sub">今日任务、专注情况、最近日记和常用导航，一眼看全。</p>
    </header>

    <p v-if="error" class="note note-error">{{ error }}</p>
    <p v-if="loading && !dashboard.data" class="note">加载中…</p>

    <div v-if="dashboard.data" class="grid">
      <!-- 今日任务 -->
      <section class="card span-2">
        <div class="card-head">
          <h2>今日任务</h2>
          <RouterLink to="/plans" class="more">去计划页 →</RouterLink>
        </div>
        <ul v-if="dashboard.data.today_tasks.length" class="task-list">
          <li v-for="task in dashboard.data.today_tasks" :key="task.id" class="task-row">
            <span class="task-title">{{ task.title }}</span>
            <span class="badge" :class="impCls[task.importance]">{{ impLabels[task.importance] }}</span>
          </li>
        </ul>
        <p v-else class="empty">今天没有未完成任务，去计划页安排一下。</p>
      </section>

      <!-- 今日专注 -->
      <section class="card">
        <div class="card-head">
          <h2>今日专注</h2>
          <RouterLink to="/pomodoro" class="more">去番茄钟 →</RouterLink>
        </div>
        <div class="focus-stat">
          <p class="focus-count">
            {{ dashboard.data.pomodoro.count }}<span class="focus-unit"> 次</span>
          </p>
          <p class="focus-duration">{{ formatDuration(dashboard.data.pomodoro.total_seconds) }}</p>
        </div>
      </section>

      <!-- 最近日记 -->
      <section class="card span-2">
        <div class="card-head">
          <h2>最近日记</h2>
          <RouterLink to="/diary" class="more">去日记 →</RouterLink>
        </div>
        <ul v-if="dashboard.data.recent_diaries.length" class="diary-list">
          <li v-for="entry in dashboard.data.recent_diaries" :key="entry.id" class="diary-row">
            <RouterLink to="/diary" class="diary-link">
              <span class="diary-date">{{ entry.date }}</span>
              <span class="diary-title">{{ entry.title }}</span>
<span v-for="tag in entry.tags" :key="tag" class="tag-sm">{{ tag }}</span>
            </RouterLink>
          </li>
        </ul>
        <p v-else class="empty">还没有日记，去日记页写第一篇吧。</p>
      </section>

      <!-- 置顶导航 -->
      <section class="card">
        <div class="card-head">
          <h2>常用导航</h2>
          <RouterLink to="/nav" class="more">去导航 →</RouterLink>
        </div>
        <ul v-if="dashboard.data.pinned_links.length" class="link-list">
          <li v-for="link in dashboard.data.pinned_links" :key="link.id">
            <a class="link-row" :href="link.url" target="_blank" rel="noopener">
              <span class="link-icon">
                <img
                  v-if="!iconFailed.has(link.id)"
                  :src="faviconUrl(link.url)"
                  alt=""
                  loading="lazy"
                  @error="handleIconError(link.id)"
                />
                <span v-else class="link-fallback">{{ initials(link.title) }}</span>
              </span>
              <span class="link-meta">
                <span class="link-title">{{ link.title }}</span>
                <span class="link-domain">{{ domainOf(link.url) }}</span>
              </span>
            </a>
          </li>
        </ul>
        <p v-else class="empty">还没有置顶导航，去导航页把常用网站置顶吧。</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
h1,
h2 {
  font-family: var(--serif);
  font-weight: 700;
  margin: 0;
}
a {
  color: inherit;
  text-decoration: none;
}

.page-head {
  margin-bottom: 24px;
  border-bottom: 1px solid var(--hairline);
  padding-bottom: 16px;
}
.page-head h1 {
  font-size: 22px;
  letter-spacing: 2px;
}
.page-sub {
  margin: 8px 0 0;
  font-size: 14px;
  color: var(--sub);
}

.note {
  color: var(--sub);
  font-size: 14px;
  margin: 0 0 16px;
}
.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
  align-items: start;
}
.span-2 {
  grid-column: span 2;
}
.card-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 12px;
}
.card-head h2 {
  font-size: 17px;
}
.more {
  font-size: 13px;
  color: var(--teal);
}
.more:hover {
  color: var(--teal-dark);
}

.task-list,
.diary-list,
.link-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.task-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 0;
  border-bottom: 1px dashed var(--hairline);
}
.task-row:last-child {
  border-bottom: 0;
}
.task-title {
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.badge {
  flex-shrink: 0;
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 11px;
  font-weight: 700;
}

.focus-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 18px 0 8px;
}
.focus-count {
  margin: 0;
  font-family: var(--serif);
  font-size: 44px;
  font-weight: 700;
  color: var(--teal);
  line-height: 1;
}
.focus-unit {
  font-size: 18px;
}
.focus-duration {
  margin: 0;
  font-size: 14px;
  color: var(--sub);
}

.diary-row {
  padding: 8px 0;
  border-bottom: 1px dashed var(--hairline);
}
.diary-row:last-child {
  border-bottom: 0;
}
.diary-link {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.diary-date {
  flex-shrink: 0;
  font-size: 12px;
  color: var(--sub);
}
.diary-title {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.diary-link:hover .diary-title {
  color: var(--teal);
}
.link-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 0;
  border-radius: 10px;
}
.link-row:hover .link-title {
  color: var(--teal);
}
.link-icon {
  flex-shrink: 0;
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid var(--hairline);
  background: var(--teal-soft);
  display: grid;
  place-items: center;
  overflow: hidden;
}
.link-icon img {
  width: 17px;
  height: 17px;
  object-fit: contain;
}
.link-fallback {
  font-family: var(--serif);
  font-size: 13px;
  font-weight: 700;
  color: var(--teal-dark);
}
.link-meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.link-title {
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.link-domain {
  font-size: 11px;
  color: var(--sub);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty {
  margin: 4px 0 0;
  font-size: 13px;
  color: var(--sub);
}

@media (max-width: 880px) {
  .grid {
    grid-template-columns: 1fr;
  }
  .span-2 {
    grid-column: span 1;
  }
}
</style>
