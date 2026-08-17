<script setup>
import { reactive, ref, watch } from 'vue'

import BaseModal from '../BaseModal.vue'
import { useNavStore } from '../../stores/nav'

const props = defineProps({
  mode: { type: String, default: 'add' },
  editing: { type: Object, default: null },
  categories: { type: Array, default: () => [] }
})
const emit = defineEmits(['close', 'saved', 'deleted'])

const navStore = useNavStore()

const tab = ref('link')
const categoryForm = reactive({ name: '' })
const linkForm = reactive({ title: '', url: '', description: '', category_id: null, is_pinned: false })
const formError = ref('')

watch(
  () => props.editing,
  (link) => {
    linkForm.title = link?.title || ''
    linkForm.url = link?.url || ''
    linkForm.description = link?.description || ''
    linkForm.category_id = link?.category_id ?? props.categories[0]?.id ?? null
    linkForm.is_pinned = link?.is_pinned ?? false
  },
  { immediate: true }
)

function save() {
  if (tab.value === 'category') saveCategory()
  else saveLink()
}
async function saveCategory() {
  const name = categoryForm.name.trim()
  if (!name) {
    formError.value = '请输入分类名称'
    return
  }
  try {
    await navStore.createCategory(name, props.categories.length)
    emit('saved')
    emit('close')
  } catch (e) {
    formError.value = e.response?.data?.detail || '保存分类失败'
  }
}
async function saveLink() {
  if (!linkForm.title.trim() || !linkForm.url.trim() || !linkForm.category_id) {
    formError.value = '请填写标题、URL 和分类'
    return
  }
  const payload = {
    title: linkForm.title.trim(),
    url: linkForm.url.trim(),
    description: linkForm.description.trim() || null,
    category_id: linkForm.category_id,
    is_pinned: linkForm.is_pinned
  }
  try {
    if (props.mode === 'edit' && props.editing) await navStore.updateLink(props.editing.id, payload)
    else await navStore.createLink(payload)
    emit('saved')
    emit('close')
  } catch (e) {
    formError.value = e.response?.data?.detail || '保存链接失败'
  }
}
async function deleteEditingLink() {
  if (!props.editing) return
  if (!confirm(`确定删除链接「${props.editing.title}」？`)) return
  try {
    await navStore.deleteLink(props.editing.id)
    emit('deleted')
    emit('close')
  } catch (e) {
    formError.value = e.response?.data?.detail || '删除链接失败'
  }
}
</script>

<template>
  <BaseModal @close="emit('close')">
    <div class="modal">
      <div class="modal-head">
        <h3>{{ mode === 'add' ? '新增' : '编辑链接' }}</h3>
      </div>
      <div v-if="mode === 'add'" class="modal-tabs">
        <button
          type="button"
          class="modal-tab"
          :class="{ active: tab === 'category' }"
          @click="tab = 'category'"
        >
          新建分类
        </button>
        <button
          type="button"
          class="modal-tab"
          :class="{ active: tab === 'link' }"
          @click="tab = 'link'"
        >
          新建链接
        </button>
      </div>

      <form @submit.prevent="save">
        <template v-if="tab === 'category'">
          <div class="field">
            <label>分类名称</label>
            <input v-model="categoryForm.name" type="text" placeholder="例如：图片生成" />
          </div>
        </template>
        <template v-else>
          <div class="field">
            <label>标题</label>
            <input v-model="linkForm.title" type="text" placeholder="链接名称" />
          </div>
          <div class="field">
            <label>URL</label>
            <input v-model="linkForm.url" type="url" placeholder="https://" />
          </div>
          <div class="field">
            <label>描述（可选）</label>
            <input v-model="linkForm.description" type="text" />
          </div>
          <div class="field">
            <label>分类</label>
            <select v-model="linkForm.category_id">
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
            </select>
          </div>
          <label class="check-row">
            <input v-model="linkForm.is_pinned" type="checkbox" /> 置顶
          </label>
        </template>

        <p v-if="formError" class="nav-note nav-error">{{ formError }}</p>

        <div class="modal-foot">
          <button v-if="mode === 'edit'" type="button" class="btn btn-danger" @click="deleteEditingLink">
            删除
          </button>
          <button type="button" class="btn" @click="emit('close')">取消</button>
          <button type="submit" class="btn btn-primary">保存</button>
        </div>
      </form>
    </div>
  </BaseModal>
</template>

<style scoped>
.modal {
  width: 100%;
  max-width: 420px;
  padding: 22px;
  box-shadow: 0 16px 40px rgba(43, 38, 34, 0.18);
}
.modal h3 {
  font-family: var(--serif);
  font-weight: 700;
  font-size: 18px;
  margin: 0 0 14px;
}
.modal-tabs {
  display: flex;
  gap: 4px;
  background: var(--paper-soft);
  border-radius: 10px;
  padding: 4px;
  margin-bottom: 16px;
}
.modal-tab {
  flex: 1;
  padding: 7px 0;
  border-radius: 8px;
  font-size: 14px;
  color: var(--sub);
  text-align: center;
}
.modal-tab.active {
  background: var(--card);
  color: var(--teal-dark);
  font-weight: 600;
  box-shadow: 0 1px 3px rgba(43, 38, 34, 0.08);
}
.field {
  margin-bottom: 12px;
}
.field label {
  display: block;
  font-size: 13px;
  color: var(--sub);
  margin-bottom: 5px;
}
.field input,
.field select {
  width: 100%;
  border: 1px solid var(--hairline);
  border-radius: 10px;
  background: var(--card);
  padding: 9px 12px;
  font-size: 14px;
  color: var(--ink);
}
.field input:focus,
.field select:focus {
  border-color: var(--teal);
  outline: none;
  box-shadow: 0 0 0 3px var(--teal-soft);
}
.check-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--sub);
  margin-bottom: 16px;
}
.modal-foot {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.modal .btn {
  border-radius: 10px;
  padding: 8px 16px;
  font-size: 14px;
}
.btn-danger {
  margin-right: auto;
}
.nav-note {
  color: var(--sub);
  font-size: 14px;
  margin: 0 0 16px;
}
</style>
