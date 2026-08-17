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
    },
    async createCategory(name, sort_order) {
      return (await api.post('/nav/categories', { name, sort_order })).data
    },
    async createLink(payload) {
      return (await api.post('/nav/links', payload)).data
    },
    async updateLink(id, payload) {
      return (await api.put(`/nav/links/${id}`, payload)).data
    },
    async deleteLink(id) {
      await api.delete(`/nav/links/${id}`)
    }
  }
})
