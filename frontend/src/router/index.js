import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    redirect: '/dashboard',
    component: AppLayout,
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表盘', roles: ['admin', 'pv_specialist', 'cra'] }
      },
      {
        path: 'ae',
        name: 'AeCoding',
        component: () => import('../views/AeCoding.vue'),
        meta: { title: 'AE编码', roles: ['admin', 'pv_specialist', 'cra'] }
      },
      {
        path: 'sae',
        name: 'SaeReports',
        component: () => import('../views/SaeReports.vue'),
        meta: { title: 'SAE报告', roles: ['admin', 'pv_specialist', 'cra'] }
      },
      {
        path: 'deviation',
        name: 'Deviations',
        component: () => import('../views/Deviations.vue'),
        meta: { title: '方案偏离', roles: ['admin', 'pv_specialist', 'cra'] }
      },
      {
        path: 'signal',
        name: 'Signals',
        component: () => import('../views/Signals.vue'),
        meta: { title: '信号挖掘', roles: ['admin', 'pv_specialist'] }
      },
      {
        path: 'compliance',
        name: 'Compliance',
        component: () => import('../views/Compliance.vue'),
        meta: { title: '合规质控', roles: ['admin', 'pv_specialist', 'cra'] }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../views/Knowledge.vue'),
        meta: { title: '知识库', roles: ['admin', 'pv_specialist'] }
      },
      {
        path: 'audit',
        name: 'Audit',
        component: () => import('../views/Audit.vue'),
        meta: { title: '审计日志', roles: ['admin'] }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: () => import('../views/UserManagement.vue'),
        meta: { title: '用户管理', roles: ['admin'] }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('ae_token')
  if (to.path !== '/login' && !token) {
    next('/login')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router