<script setup>
import { ref } from 'vue'

import BaseModal from '../BaseModal.vue'
import { useQuizStore } from '../../stores/quiz'

const emit = defineEmits(['close'])

const quizStore = useQuizStore()

const preview = ref(null)
const manageMsg = ref('')
const managing = ref(false)

const YAML_SAMPLE = `# 分类固定写在文件顶部，整个文件一个分类
category: Python
questions:
  - type: choice          # choice=选择题（考概念）
    "no": "1.1"           # 键必须加引号，否则 YAML 会解析成布尔值
    score: 5
    title: 下面哪个是 Python 装饰器的正确理解？
    options:              # 固定 4 项，对应 A/B/C/D
      - 装饰器是接收函数并返回新函数的可调用对象   # A
      - 装饰器只能修饰类方法                      # B
      - 被 @ 装饰的函数会立即执行                 # C
      - 装饰器是 Python 3 才有的特性              # D
    answer: A             # 只能填 A/B/C/D 之一
    explanation: |
      装饰器本质是接收函数并返回新函数的可调用对象。

  - type: fill            # fill=填空题（考代码挖空）
    "no": "1.2"
    score: 10
    title: 补全装饰器：返回内部函数
    code: |
      def timer(fn):
          def wrap(*a, **kw):
              return fn(*a, **kw)
          return ____
    answer: wrap
    explanation: |
      装饰器要把 wrap 返回出去替换原函数。`

async function onQuizFile(e) {
  const file = e.target.files?.[0]
  if (!file) return
  manageMsg.value = ''
  preview.value = null
  try {
    preview.value = await quizStore.previewImport(file)
  } catch (err) {
    manageMsg.value = err.response?.data?.detail || '解析失败'
  } finally {
    e.target.value = ''
  }
}
async function confirmImport() {
  if (!preview.value || !preview.value.items.length || managing.value) return
  managing.value = true
  try {
    const result = await quizStore.confirmImport(preview.value.items)
    manageMsg.value = `导入成功：新增 ${result.imported} 题、更新 ${result.updated} 题`
    preview.value = null
    quizStore.refresh()
  } catch (err) {
    manageMsg.value = err.response?.data?.detail || '导入失败'
  } finally {
    managing.value = false
  }
}
</script>

<template>
  <BaseModal @close="emit('close')">
    <div class="flex max-h-[85vh] w-full max-w-xl flex-col rounded-2xl border border-hairline bg-card p-6 shadow-xl">
      <h3 class="mb-2 font-serif text-lg text-ink">题库管理</h3>
      <p class="mb-3 text-[13px] text-sub">
        让 AI 按固定格式生成题目后快速导入。分类写在文件顶部，整个文件一个分类；选择题考概念、填空题考代码挖空。
      </p>
      <pre class="min-h-0 flex-1 overflow-auto rounded-lg border border-hairline bg-paper-soft p-3 text-xs leading-relaxed">{{ YAML_SAMPLE }}</pre>
      <div class="mt-3 flex flex-wrap gap-2">
        <label class="cursor-pointer rounded-lg bg-teal px-4 py-2 text-sm font-medium text-card hover:bg-teal-dark">
          导入题目
          <input type="file" accept=".yaml,.yml,.md,.txt" class="hidden" @change="onQuizFile">
        </label>
        <button class="rounded-lg border border-hairline px-4 py-2 text-sm hover:border-teal hover:text-teal" @click="quizStore.downloadTemplate()">
          下载题目格式文档
        </button>
        <button class="rounded-lg border border-hairline px-4 py-2 text-sm hover:border-teal hover:text-teal" @click="emit('close')">关闭</button>
      </div>

      <div v-if="preview" class="mt-3 rounded-lg bg-paper-soft p-3 text-[13px]">
        <p>分类：<span class="font-medium text-teal-dark">{{ preview.category || '—' }}</span></p>
        <p>新增 {{ preview.new.length }} 题、更新 {{ preview.updated.length }} 题</p>
        <p v-if="preview.errors.length" class="text-red">错误：{{ preview.errors.join('；') }}</p>
        <button
          v-if="preview.items.length"
          class="mt-2 rounded-lg bg-teal px-4 py-1.5 text-sm font-medium text-card hover:bg-teal-dark disabled:opacity-50"
          :disabled="managing"
          @click="confirmImport"
        >
          {{ managing ? '导入中…' : '确认导入 ' + preview.items.length + ' 题' }}
        </button>
      </div>
      <p v-if="manageMsg" class="mt-3 text-xs text-teal-dark">{{ manageMsg }}</p>
    </div>
  </BaseModal>
</template>
