import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', name: 'home', component: () => import('../views/HomeView.vue'), meta: { title: '首页' } },
  { path: '/plans', name: 'plans', component: () => import('../views/PlansView.vue'), meta: { title: '计划' } },
  { path: '/diary', name: 'diary', component: () => import('../views/DiaryView.vue'), meta: { title: '日记' } },
  { path: '/pomodoro', name: 'pomodoro', component: () => import('../views/PomodoroView.vue'), meta: { title: '番茄钟' } },
  { path: '/notes', name: 'notes', component: () => import('../views/NotesView.vue'), meta: { title: '笔记' } },
  { path: '/nav', name: 'nav', component: () => import('../views/NavView.vue'), meta: { title: '导航' } }
]

export default createRouter({
  history: createWebHistory(),
  routes
})
