<script setup>
import { useRoute } from 'vue-router'

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
  <div class="flex min-h-screen">
    <aside class="w-48 shrink-0 border-r border-gray-200 bg-white px-4 py-6">
      <h1 class="mb-6 text-lg font-bold">个人网站</h1>
      <nav class="flex flex-col gap-1">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="rounded px-3 py-2 text-sm hover:bg-gray-100"
          :class="{ 'bg-blue-50 font-medium text-blue-600': route.path === item.path }"
        >
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="flex-1 p-8">
      <RouterView />
    </main>
  </div>
</template>
