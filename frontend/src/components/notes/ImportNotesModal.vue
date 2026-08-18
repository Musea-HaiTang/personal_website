<script setup>
import { computed, ref } from 'vue'

import BaseModal from '../BaseModal.vue'
import { useNotesStore } from '../../stores/notes'

const emit = defineEmits(['close', 'imported'])

const notesStore = useNotesStore()

const importTab = ref('paste')
const pTitle = ref('')
const pContent = ref('')
const folderSel = ref('未分类')
const folderCreateOpen = ref(false)
const newFolderName = ref('')
const folderError = ref('')
const folderSaving = ref(false)
const uploadFiles = ref([])
const dirFiles = ref([])
const dragActive = ref(false)
const importMsg = ref('')
const importing = ref(false)

const folderOptions = computed(() => {
  const names = new Set(['未分类', ...notesStore.folders.map((f) => f.folder), folderSel.value])
  return [...names]
})
const targetFolder = computed(() => folderSel.value)

function openFolderCreate() {
  newFolderName.value = ''
  folderError.value = ''
  folderCreateOpen.value = true
}
async function confirmNewFolder() {
  const name = newFolderName.value.trim()
  if (!name) {
    folderError.value = '请输入分类名称'
    return
  }
  if (notesStore.folders.some((f) => f.folder === name)) {
    folderSel.value = name
    folderCreateOpen.value = false
    newFolderName.value = ''
    folderError.value = ''
    return
  }
  if (folderSaving.value) return
  folderSaving.value = true
  folderError.value = ''
  try {
    await notesStore.createFolder(name)
    folderSel.value = name
    folderCreateOpen.value = false
    newFolderName.value = ''
  } catch (e) {
    folderError.value = e.response?.data?.detail || '新增分类失败'
  } finally {
    folderSaving.value = false
  }
}

function onUploadDrop(e) {
  e.preventDefault()
  dragActive.value = false
  uploadFiles.value = [...e.dataTransfer.files]
}
function onUploadChange(e) {
  uploadFiles.value = [...e.target.files]
}
function onDirDrop(e) {
  e.preventDefault()
  dragActive.value = false
  dirFiles.value = [...e.dataTransfer.files]
}
function onDirChange(e) {
  dirFiles.value = [...e.target.files]
}
function removeUploadFile(i) {
  uploadFiles.value = uploadFiles.value.filter((_, idx) => idx !== i)
}
function removeDirFile(i) {
  dirFiles.value = dirFiles.value.filter((_, idx) => idx !== i)
}

function finishImport(message) {
  emit('imported', message)
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
      content: pContent.value
    })
    finishImport('已创建笔记')
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
    finishImport(parts.join('；'))
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
        <button
          class="whitespace-nowrap rounded-lg border border-teal px-3 py-2 text-sm text-teal hover:bg-teal hover:text-card"
          @click="openFolderCreate"
        >
          新增分类
        </button>
      </div>

      <template v-if="importTab === 'paste'">
        <input v-model="pTitle" class="mb-2 w-full rounded-lg border border-hairline bg-card px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="笔记标题">
        <textarea v-model="pContent" class="h-36 w-full resize-none rounded-lg border border-hairline bg-card px-3 py-2 text-sm focus:border-teal focus:outline-none" placeholder="正文（Markdown）" />
      </template>
      <template v-else-if="importTab === 'upload'">
        <label
          class="block cursor-pointer rounded-xl border border-dashed p-8 text-center text-sm text-sub hover:border-teal hover:text-teal"
          :class="dragActive ? 'border-teal bg-teal-soft' : 'border-hairline'"
          @dragover.prevent="dragActive = true"
          @dragleave.prevent="dragActive = false"
          @drop.prevent="onUploadDrop"
        >
          点击选择或拖拽 .md 文件（可多选）
          <input type="file" multiple accept=".md,.markdown,.txt" class="hidden" @change="onUploadChange">
        </label>
        <div v-if="uploadFiles.length" class="mt-2 max-h-32 overflow-auto rounded-lg border border-hairline bg-card p-2 text-xs text-sub">
          <div v-for="(f, i) in uploadFiles" :key="`${f.name}-${i}`" class="flex items-center justify-between gap-2 py-1">
            <span class="min-w-0 truncate">{{ f.name }}</span>
            <button type="button" class="shrink-0 rounded px-1.5 text-red hover:bg-red-soft" @click="removeUploadFile(i)">移除</button>
          </div>
        </div>
      </template>
      <template v-else>
        <label
          class="block cursor-pointer rounded-xl border border-dashed p-8 text-center text-sm text-sub hover:border-teal hover:text-teal"
          :class="dragActive ? 'border-teal bg-teal-soft' : 'border-hairline'"
          @dragover.prevent="dragActive = true"
          @dragleave.prevent="dragActive = false"
          @drop.prevent="onDirDrop"
        >
          选择一个本地文件夹，批量导入其中的 .md 文件
          <input type="file" webkitdirectory multiple class="hidden" @change="onDirChange">
        </label>
        <div v-if="dirFiles.length" class="mt-2 max-h-32 overflow-auto rounded-lg border border-hairline bg-card p-2 text-xs text-sub">
          <div v-for="(f, i) in dirFiles" :key="`${f.name}-${i}`" class="flex items-center justify-between gap-2 py-1">
            <span class="min-w-0 truncate">{{ f.webkitRelativePath || f.name }}</span>
            <button type="button" class="shrink-0 rounded px-1.5 text-red hover:bg-red-soft" @click="removeDirFile(i)">移除</button>
          </div>
        </div>
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

    <BaseModal v-if="folderCreateOpen" @close="folderCreateOpen = false">
      <form class="w-full max-w-sm rounded-2xl border border-hairline bg-card p-6 shadow-xl" @submit.prevent="confirmNewFolder">
        <h3 class="mb-3 font-serif text-lg text-ink">新增分类</h3>
        <input
          v-model="newFolderName"
          class="w-full rounded-lg border border-hairline bg-card px-3 py-2 text-sm focus:border-teal focus:outline-none"
          placeholder="分类名称"
          autofocus
          @keydown.esc="folderCreateOpen = false"
        >
        <p v-if="folderError" class="mt-2 text-xs text-red">{{ folderError }}</p>
        <div class="mt-4 flex justify-end gap-2">
          <button type="button" class="rounded-lg border border-hairline px-4 py-1.5 text-sm hover:border-teal hover:text-teal" @click="folderCreateOpen = false">
            取消
          </button>
          <button type="submit" class="rounded-lg bg-teal px-4 py-1.5 text-sm font-medium text-card hover:bg-teal-dark disabled:opacity-50" :disabled="folderSaving">
            {{ folderSaving ? '新增中…' : '新增' }}
          </button>
        </div>
      </form>
    </BaseModal>
  </BaseModal>
</template>
