<script setup>
import { useRoute } from 'vue-router'

import FloatingTimer from './components/FloatingTimer.vue'

const route = useRoute()

const navItems = [
  { path: '/', label: '首页' },
  { path: '/plans', label: '计划' },
  { path: '/diary', label: '日记' },
  { path: '/pomodoro', label: '番茄钟' },
  { path: '/nav', label: '导航' }
]
</script>

<template>
  <div class="flex min-h-screen bg-paper">
    <aside class="w-48 shrink-0 border-r border-hairline bg-card px-4 py-6">
      <h1 class="mb-6 font-serif text-xl font-bold tracking-wide text-ink">个人网站</h1>
      <nav class="flex flex-col gap-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="rounded px-3 py-2 text-sm text-sub hover:bg-paper-soft hover:text-ink"
          :class="{ 'bg-teal-soft font-medium text-teal': route.path === item.path }"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="flex-1 p-8">
      <RouterView />
    </main>
    <FloatingTimer />
  </div>
</template>
