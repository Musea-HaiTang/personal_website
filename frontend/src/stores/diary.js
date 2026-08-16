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
    }
  }
})
