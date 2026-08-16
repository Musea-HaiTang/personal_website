import { defineStore } from 'pinia'

import api from '../api'

export const useNavStore = defineStore('nav', {
  state: () => ({
    categories: [],
    loaded: false,
    error: ''
  }),
  actions: {
    async refresh() {
      this.error = ''
      try {
        const { data } = await api.get('/nav/categories')
        this.categories = data
        this.loaded = true
      } catch (e) {
        this.error = e.response?.data?.detail || '加载导航数据失败'
      }
    }
  }
})
