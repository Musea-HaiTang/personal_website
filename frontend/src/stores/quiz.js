import { defineStore } from 'pinia'

import api from '../api'

export const useQuizStore = defineStore('quiz', {
  state: () => ({
    questions: [],
    loaded: false,
    error: ''
  }),
  actions: {
    async refresh() {
      this.error = ''
      try {
        this.questions = (await api.get('/quiz/questions')).data
        this.loaded = true
      } catch (e) {
        this.error = e.response?.data?.detail || '加载题库失败'
      }
    },
    async previewImport(file) {
      const fd = new FormData()
      fd.append('file', file)
      return (await api.post('/quiz/import', fd)).data
    },
    async confirmImport(items) {
      return (await api.post('/quiz/import/confirm', { items })).data
    },
    async downloadTemplate() {
      const resp = await api.get('/quiz/template', { responseType: 'blob' })
      const url = URL.createObjectURL(resp.data)
      const a = document.createElement('a')
      a.href = url
      a.download = 'quiz-template.yaml'
      a.click()
      URL.revokeObjectURL(url)
    }
  }
})
