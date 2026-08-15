<script setup>
import { onMounted, ref } from 'vue'
import api from '../api'

const health = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    const { data } = await api.get('/health')
    health.value = data
  } catch {
    error.value = '后端服务未连接，请确认已运行 start.bat'
  }
})
</script>

<template>
  <div>
    <h2 class="mb-4 font-serif text-2xl font-bold text-ink">聚合首页</h2>
    <p class="mb-6 text-sub">这里将汇总今日任务、专注时长、最近日记和常用导航。</p>
    <div class="rounded-lg border border-hairline bg-card p-4">
      <p class="font-medium">系统状态</p>
      <p v-if="health" class="mt-1 text-sm text-sub">
        后端正常 · 时区 {{ health.timezone }} · 登录开关 {{ health.auth_enabled ? '开' : '关' }}
      </p>
      <p v-else-if="error" class="mt-1 text-sm text-red">{{ error }}</p>
      <p v-else class="mt-1 text-sm text-sub">检查中…</p>
    </div>
  </div>
</template>
