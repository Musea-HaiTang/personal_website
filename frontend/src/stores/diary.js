import { defineStore } from 'pinia'

import api from '../api'

export const useDiaryStore = defineStore('diary', {
  state: () => ({
    entries: [],
    flashes: [],
    loaded: false,
    error: ''
  }),
  actions: {
    async refresh() {
      this.error = ''
      try {
        const [d, f] = await Promise.all([api.get('/diary'), api.get('/flash')])
        this.entries = d.data
        this.flashes = f.data
        this.loaded = true
      } catch (e) {
        this.error = e.response?.data?.detail || '加载日记数据失败'
      }
    },
    async saveDiary(payload, id = null) {
      if (id) return (await api.put(`/diary/${id}`, payload)).data
      return (await api.post('/diary', payload)).data
    },
    async deleteDiary(id) {
      await api.delete(`/diary/${id}`)
    },
    async createFlash(content) {
      return (await api.post('/flash', { content })).data
    },
    async deleteFlash(id) {
      await api.delete(`/flash/${id}`)
    }
  }
})
