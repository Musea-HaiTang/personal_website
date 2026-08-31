import { defineStore } from 'pinia'

import api from '../api'

export const useNotesStore = defineStore('notes', {
  state: () => ({
    notes: [],
    folders: [],
    loaded: false,
    folder: 'all',
    kw: '',
    error: ''
  }),
  getters: {
    // 笔记总数（各分类计数之和），用于「全部」页签的稳定计数，不随关键词变化。
    total() {
      return this.folders.reduce((sum, f) => sum + f.count, 0)
    },
    // 分类在本地筛（即时切页签）；关键词已交给后端。
    filtered() {
      if (this.folder === 'all') return this.notes
      return this.notes.filter((n) => n.folder === this.folder)
    }
  },
  actions: {
    async refresh() {
      this.error = ''
      try {
        const params = {}
        if (this.kw.trim()) params.q = this.kw.trim()
        const [notes, folders] = await Promise.all([
          api.get('/notes', { params }),
          api.get('/notes/folders')
        ])
        this.notes = notes.data
        this.folders = folders.data
        this.loaded = true
      } catch (e) {
        this.error = e.response?.data?.detail || '加载笔记失败'
      }
    },
    async fetchNote(id) {
      const { data } = await api.get(`/notes/${id}`)
      return data
    },
    async create(payload) {
      return (await api.post('/notes', payload)).data
    },
    async createFolder(name) {
      const folder = (await api.post('/notes/folders', { name })).data
      if (!this.folders.some((f) => f.folder === folder.folder)) {
        this.folders = [...this.folders, folder].sort((a, b) => a.folder.localeCompare(b.folder, 'zh'))
      }
      return folder
    },
    async remove(id) {
      await api.delete(`/notes/${id}`)
    },
    async importFiles(folder, files) {
      const fd = new FormData()
      fd.append('folder', folder)
      files.forEach((f) => fd.append('files', f))
      return (await api.post('/notes/import', fd)).data
    }
  }
})
