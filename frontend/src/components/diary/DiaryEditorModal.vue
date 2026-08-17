<script setup>
import { computed, ref, watch } from 'vue'

import { useDiaryStore } from '../../stores/diary'

const props = defineProps({
  diary: { type: Object, default: null },
  today: { type: String, default: '' },
  saving: { type: Boolean, default: false }
})
const emit = defineEmits(['save', 'delete', 'close'])

const diaryStore = useDiaryStore()

const editTitle = ref('')
const editContent = ref('')
const selectedTags = ref([])
const showTagPop = ref(false)
const newTag = ref('')

const editWords = computed(() => editContent.value.replace(/\s/g, '').length)
const allTags = computed(() => [...new Set(diaryStore.entries.flatMap((e) => e.tags || []))].sort())
const dateLabel = computed(() => {
  const d = new Date(props.today + 'T00:00:00')
  return `${d.getMonth() + 1}月${d.getDate()}日 · 星期${'日一二三四五六'[d.getDay()]}`
})

watch(
  () => props.diary,
  (diary) => {
    editTitle.value = diary?.title || ''
    editContent.value = diary?.content || ''
    selectedTags.value = [...(diary?.tags || [])]
    showTagPop.value = false
  },
  { immediate: true }
)

function toggleTag(t) {
  selectedTags.value = selectedTags.value.includes(t) ? selectedTags.value.filter((x) => x !== t) : [...selectedTags.value, t]
}
function removeTag(t) {
  selectedTags.value = selectedTags.value.filter((x) => x !== t)
}
function addNewTag() {
  const v = newTag.value.trim()
  if (!v) return
  if (!selectedTags.value.includes(v)) selectedTags.value.push(v)
  newTag.value = ''
}
function submit() {
  emit('save', {
    date: props.today,
    title: editTitle.value.trim() || '无标题',
    tags: selectedTags.value,
    content: editContent.value
  })
}
</script>

<template>
  <div class="edit-overlay" @click.self="emit('close')">
    <div class="paper letter edit-modal">
      <div class="head edit-head">
        <input v-model="editTitle" class="title-input" placeholder="标题">
        <div class="date">{{ dateLabel }}</div>
      </div>
      <div class="edit-scroll" @click="showTagPop = false">
        <div class="tag-zone" @click.stop>
          <div class="tag-selected">
            <span v-for="t in selectedTags" :key="t" class="tag-chip">{{ t }}<button type="button" @click="removeTag(t)">×</button></span>
          </div>
          <button type="button" class="btn tag-open" @click="showTagPop = !showTagPop">＋ 标签</button>
          <div v-if="showTagPop" class="tag-pop">
            <h5>常用标签</h5>
            <div class="tag-pop-list">
              <button v-for="t in allTags" :key="t" type="button" class="tag-opt" :class="{ on: selectedTags.includes(t) }" @click="toggleTag(t)">{{ t }}</button>
            </div>
            <div class="tag-pop-add">
              <input v-model="newTag" placeholder="新标签" @keydown.enter="addNewTag">
              <button type="button" @click="addNewTag">添加</button>
            </div>
          </div>
        </div>
        <textarea v-model="editContent" class="edit-content" rows="14" placeholder="用 Markdown 写今天的日记…"></textarea>
      </div>
      <div class="ed-actions">
        <span class="wc">已写 {{ editWords.toLocaleString() }} 字</span>
        <button v-if="diary" type="button" class="btn danger" @click="emit('delete')">删除</button>
        <button type="button" class="btn" @click="emit('close')">取消</button>
        <button type="button" class="btn btn-teal" :disabled="saving" @click="submit">{{ saving ? '保存中…' : '保存' }}</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.edit-overlay {
  position: fixed;
  inset: 0;
  background: rgba(43, 38, 34, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 50;
  padding: 24px;
}
.paper {
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(43, 38, 34, 0.05);
}
.letter {
  position: relative;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: box-shadow 0.15s;
  background: #fdfbf7;
  font-family: var(--kai);
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(43, 38, 34, 0.05), inset 0 0 60px rgba(183, 121, 31, 0.025);
}
.head {
  position: relative;
  padding: 16px 24px 12px;
}
.head::before {
  content: "";
  position: absolute;
  left: 24px;
  right: 24px;
  bottom: 0;
  height: 1px;
  background: #e8e2d4;
}
.head::after {
  content: "记";
  position: absolute;
  top: 12px;
  right: 20px;
  width: 26px;
  height: 26px;
  background: var(--teal);
  color: #fff;
  font-family: "Songti SC", "STSong", SimSun, serif;
  font-size: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 5px;
  transform: rotate(-4deg);
  box-shadow: 0 1px 2px rgba(43, 38, 34, 0.18);
  line-height: 1;
}
.head .date {
  font-size: 14px;
  color: var(--sub);
  flex-shrink: 0;
  letter-spacing: 0.03em;
  padding-bottom: 2px;
}
.btn {
  border: 1px solid var(--hairline);
  background: var(--card);
  color: var(--ink);
  border-radius: 8px;
  padding: 7px 12px;
  font-size: 13px;
  cursor: pointer;
}
.btn:hover {
  border-color: var(--teal);
  color: var(--teal);
}
.btn-teal {
  background: var(--teal);
  border-color: var(--teal);
  color: #fff;
}
.btn-teal:hover {
  background: var(--teal-dark);
  border-color: var(--teal-dark);
  color: #fff;
}
.btn-teal:disabled {
  opacity: 0.6;
  cursor: default;
}
.btn.danger {
  color: var(--red);
  border-color: var(--red);
}
.tag-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  background: var(--teal-soft);
  color: var(--teal);
  border: 1px solid var(--teal);
  border-radius: 999px;
  padding: 2px 9px;
  font-size: 13px;
}
.tag-chip button {
  background: none;
  border: none;
  color: var(--teal);
  font-size: 12px;
  padding: 0 0 0 2px;
  cursor: pointer;
}
.edit-modal {
  width: min(680px, 100%);
  max-height: 88vh;
  box-shadow: 0 24px 70px rgba(43, 38, 34, 0.4);
  background: #fdfbf7;
  display: flex;
  flex-direction: column;
}
.edit-head {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 14px 24px 10px;
}
.edit-head::before {
  display: none;
}
.edit-head .date {
  margin-right: 34px;
}
.title-input {
  flex: 1;
  min-width: 0;
  border: none;
  border-bottom: 1px dashed var(--hairline);
  background: transparent;
  font-family: var(--kai);
  font-size: 22px;
  font-weight: 700;
  padding: 2px 2px 6px;
  outline: none;
}
.edit-scroll {
  flex: 1;
  overflow: auto;
  padding: 12px 24px 18px;
}
.tag-zone {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.tag-selected {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.tag-pop {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 30;
  width: 300px;
  background: var(--card);
  border: 1px solid var(--hairline);
  border-radius: 12px;
  box-shadow: 0 12px 32px rgba(43, 38, 34, 0.16);
  padding: 14px;
}
.tag-pop h5 {
  font-size: 12px;
  color: var(--sub);
  margin: 0 0 8px;
}
.tag-pop-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}
.tag-opt {
  border: 1px solid var(--hairline);
  background: var(--card);
  color: var(--sub);
  border-radius: 999px;
  padding: 3px 11px;
  font-size: 13px;
  cursor: pointer;
}
.tag-opt.on {
  background: var(--teal-soft);
  border-color: var(--teal);
  color: var(--teal);
  font-weight: 600;
}
.tag-pop-add {
  display: flex;
  gap: 6px;
}
.tag-pop-add input {
  flex: 1;
  min-width: 0;
  border: 1px solid var(--hairline);
  border-radius: 6px;
  padding: 5px 9px;
  font-size: 13px;
  outline: none;
}
.tag-pop-add button {
  border: 1px solid var(--hairline);
  background: var(--card);
  border-radius: 6px;
  padding: 5px 10px;
  font-size: 13px;
  color: var(--ink);
  cursor: pointer;
}
.edit-content {
  width: 100%;
  min-height: 300px;
  border: none;
  resize: vertical;
  font-family: var(--kai);
  font-size: 16px;
  line-height: 30px;
  outline: none;
  padding: 6px 0;
  background: repeating-linear-gradient(to bottom, transparent 0 29px, #ece7da 29px 30px);
}
.ed-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  align-items: center;
  padding: 12px 22px;
  border-top: 1px solid var(--hairline);
}
.wc {
  font-size: 12px;
  color: var(--sub);
  margin-right: auto;
}
</style>
