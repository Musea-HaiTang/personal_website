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
    async refresh() {
      this.error = ''
      try {
        const [plansRes, todayRes, allRes] = await Promise.all([
          api.get('/plans', { params: { week_start: weekStart } }),
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
    }
  }
})
