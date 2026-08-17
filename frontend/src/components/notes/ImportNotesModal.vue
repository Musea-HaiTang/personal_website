<script setup>
import { computed, ref } from 'vue'

import BaseModal from '../BaseModal.vue'
import { useNotesStore } from '../../stores/notes'

const emit = defineEmits(['close', 'imported'])

const notesStore = useNotesStore()

const importTab = ref('paste')
const pTitle = ref('')
const pTags = ref('')
const pContent = ref('')
const folderSel = ref('未分类')
const folderNew = ref('')
const uploadFiles = ref([])
const dirFiles = ref([])
const importMsg = ref('')
const importing = ref(false)

const folderOptions = computed(() => ['未分类', ...notesStore.folders.map((f) => f.folder)])
const targetFolder = computed(() => folderNew.value.trim() || folderSel.value)

function onUploadChange(e) {
  uploadFiles.value = [...e.target.files]
}
function onDirChange(e) {
  dirFiles.value = [...e.target.files]
}
async function doPaste() {
  const title = pTitle.value.trim()
  if (!title) {
    importMsg.value = '请填写笔记标题'
    return
  }
  importing.value = true
  importMsg.value = ''
  try {
    await notesStore.create({
      title,
      folder: targetFolder.value,
      tags: pTags.value.split(/[,，]/).map((t) => t.trim()).filter(Boolean),
      content: pContent.value
    })
    importMsg.value = '已创建笔记'
    pTitle.value = ''
    pTags.value = ''
    pContent.value = ''
    emit('imported')
  } catch (e) {
    importMsg.value = e.response?.data?.detail || '创建失败'
  } finally {
    importing.value = false
  }
}
async function doImport(files) {
  if (!files.length) {
    importMsg.value = '请先选择 .md 文件'
    return
  }
  importing.value = true
  importMsg.value = ''
  try {
    const result = await notesStore.importFiles(targetFolder.value, files)
    const parts = [`已导入 ${result.created.length} 篇`]
    if (result.renamed.length) parts.push(`自动改名：${result.renamed.join('、')}`)
    if (result.errors.length) parts.push(`失败：${result.errors.join('；')}`)
    importMsg.value = parts.join('；')
    uploadFiles.value = []
    dirFiles.value = []
    emit('imported')
  } catch (e) {
    importMsg.value = e.response?.data?.detail || '导入失败'
  } finally {
    importing.value = false
  }
}
</script>

<template>
  <BaseModal @close="emit('close')">
    <div class="w-full max-w-md rounded-2xl border border-hairline bg-card p-6 shadow-xl">
      <h3 class="mb-3 font-serif text-lg text-ink">导入笔记</h3>
      <div class="mb-4 flex gap-1 rounded-xl bg-paper-soft p-1">
        <button
          v-for="t in [['paste', '粘贴新建'], ['upload', '上传文件'], ['folder', '批量导入文件夹']]"
          :key="t[0]"
          class="flex-1 rounded-lg py-1.5 text-sm"
          :class="importTab === t[0] ? 'bg-card font-semibold text-teal shadow-sm' : 'text-sub'"
          @click="importTab = t[0]"
        >
          {{ t[1] }}
        </button>
      </div>

      <div class="mb-3 flex gap-2">
        <select v-model="folderSel" class="flex-1 rounded-lg border border-hairline bg-card px-2.5 py-2 text-sm focus:border-teal focus:outline-none">
          <option v-for="f in folderOptions" :key="f" :value="f">{{ f }}</option>
        </select>
        <input v-model="folderNew" class="flex-1 rounded-lg border border-hairline bg-card px-2.5 py-2 text-sm placeholder:text-sub focus:border-teal focus:outline-none" placeholder="新文件夹（可选）">
      </div>

      <template v-if="importTab === 'paste'">
        <input v-model="pTitle" class="mb-2 w-full rounded-lg border border-hairline bg-card px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="笔记标题">
        <input v-model="pTags" class="mb-2 w-full rounded-lg border border-hairline bg-card px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="标签（逗号分隔，可选）">
        <textarea v-model="pContent" class="h-36 w-full resize-none rounded-lg border border-hairline bg-card px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="正文（Markdown）" />
      </template>
      <template v-else-if="importTab === 'upload'">
        <label class="block cursor-pointer rounded-xl border border-dashed border-hairline p-8 text-center text-sm text-sub hover:border-teal hover:text-teal">
          点击选择或拖拽 .md 文件（可多选）
          <input type="file" multiple accept=".md,.markdown,.txt" class="hidden" @change="onUploadChange">
        </label>
        <p v-if="uploadFiles.length" class="mt-2 text-xs text-sub">已选择 {{ uploadFiles.length }} 个文件</p>
      </template>
      <template v-else>
        <label class="block cursor-pointer rounded-xl border border-dashed border-hairline p-8 text-center text-sm text-sub hover:border-teal hover:text-teal">
          选择一个本地文件夹，批量导入其中的 .md 文件
          <input type="file" webkitdirectory multiple class="hidden" @change="onDirChange">
        </label>
        <p v-if="dirFiles.length" class="mt-2 text-xs text-sub">已选择 {{ dirFiles.length }} 个文件（按所选文件夹归入）</p>
      </template>

      <p v-if="importMsg" class="mt-3 text-xs text-teal-dark">{{ importMsg }}</p>
      <div class="mt-4 flex justify-end gap-2">
        <button class="rounded-lg border border-hairline px-4 py-1.5 text-sm hover:border-teal hover:text-teal" @click="emit('close')">取消</button>
        <button
          class="rounded-lg bg-teal px-4 py-1.5 text-sm font-medium text-card hover:bg-teal-dark disabled:opacity-50"
          :disabled="importing"
          @click="importTab === 'paste' ? doPaste() : importTab === 'upload' ? doImport(uploadFiles) : doImport(dirFiles)"
        >
          {{ importing ? '处理中…' : '导入' }}
        </button>
      </div>
    </div>
  </BaseModal>
</template>
