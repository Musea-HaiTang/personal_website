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
    filtered() {
      const kw = this.kw.trim().toLowerCase()
      return this.notes.filter((n) => {
        if (this.folder !== 'all' && n.folder !== this.folder) return false
        if (!kw) return true
        return (n.title + ' ' + (n.tags || []).join(' ') + ' ' + n.content).toLowerCase().includes(kw)
      })
    }
  },
  actions: {
    async refresh() {
      this.error = ''
      try {
        const [notes, folders] = await Promise.all([api.get('/notes'), api.get('/notes/folders')])
        this.notes = notes.data
        this.folders = folders.data
        this.loaded = true
      } catch (e) {
        this.error = e.response?.data?.detail || '加载笔记失败'
      }
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
