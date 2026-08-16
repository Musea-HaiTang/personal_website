import { defineStore } from 'pinia'

import api from '../api'

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    data: null,
    error: ''
  }),
  actions: {
    async refresh() {
      this.error = ''
      try {
        const { data } = await api.get('/dashboard')
        this.data = data
      } catch (e) {
        this.error = e.response?.data?.detail || '加载首页数据失败'
      }
    }
  }
})
