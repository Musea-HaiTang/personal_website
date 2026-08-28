import { defineStore } from 'pinia'

import api from '../api'
import { today, weekStart } from '../utils/date'

export const usePlansStore = defineStore('plans', {
  state: () => ({
    plans: [],
    todayTasks: [],
    allTasks: [],
    loaded: false,
    error: ''
  }),
  actions: {
    async refresh(weekStartParam = null) {
      this.error = ''
      const ws = weekStartParam || weekStart
      try {
        const [plansRes, todayRes, allRes] = await Promise.all([
          api.get('/plans', { params: { week_start: ws } }),
          api.get('/tasks', { params: { date: today } }),
          api.get('/tasks')
        ])
        this.plans = plansRes.data
        this.todayTasks = todayRes.data
        this.allTasks = allRes.data
        this.loaded = true
      } catch (e) {
        this.error = e.response?.data?.detail || '加载失败'
      }
    },
    async savePlan(payload) {
      if (payload.id) return (await api.put(`/plans/${payload.id}`, payload)).data
      return (await api.post('/plans', payload)).data
    },
    async deletePlan(id) {
      await api.delete(`/plans/${id}`)
    },
    async saveSubtask(payload) {
      const { plan_id, ...body } = payload
      if (payload.id) return (await api.put(`/subtasks/${payload.id}`, body)).data
      return (await api.post(`/plans/${plan_id}/subtasks`, body)).data
    },
    async updateSubtask(id, payload) {
      return (await api.put(`/subtasks/${id}`, payload)).data
    },
    async deleteSubtask(id) {
      await api.delete(`/subtasks/${id}`)
    },
    async saveTask(payload) {
      if (payload.id) return (await api.put(`/tasks/${payload.id}`, payload)).data
      return (await api.post('/tasks', payload)).data
    },
    async updateTask(id, payload) {
      return (await api.put(`/tasks/${id}`, payload)).data
    },
    async deleteTask(id) {
      await api.delete(`/tasks/${id}`)
    },
    async rolloverTask(id, note) {
      if (note) await api.put(`/tasks/${id}`, { review_note: note })
      return (await api.post(`/tasks/${id}/rollover`)).data
    },
    async exportWeek(weekStartParam = null) {
      const ws = weekStartParam || weekStart
      const { data } = await api.get('/plans/week/export', {
        params: { week_start: ws },
        responseType: 'blob',
      })
      const url = URL.createObjectURL(data)
      const a = document.createElement('a')
      a.href = url
      a.download = `周计划-${ws}.md`
      a.click()
      URL.revokeObjectURL(url)
    },
    async fetchStats(weeks = 12) {
      const { data } = await api.get('/plans/stats', { params: { weeks } })
      return data
    },
    async fetchSummary(weekStart) {
      const { data } = await api.get(`/plans/${weekStart}/summary`)
      return data
    },
    async saveSummary(weekStart, payload) {
      const { data } = await api.put(`/plans/${weekStart}/summary`, payload)
      return data
    }
  }
})
