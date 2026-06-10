import { createRouter, createWebHistory } from 'vue-router'
import AppLayout from '../components/AppLayout.vue'

const routes = [
  {
    path: '/',
    redirect: () => {
      const token = localStorage.getItem('ae_token')
      return token ? '/dashboard' : '/login'
    }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/',
    component: AppLayout,
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('../views/Dashboard.vue'),
        meta: { title: '仪表盘' }
      },
      {
        path: 'ae',
        name: 'AeCoding',
        component: () => import('../views/AeCoding.vue'),
        meta: { title: 'AE编码' }
      },
      {
        path: 'sae',
        name: 'SaeReports',
        component: () => import('../views/SaeReports.vue'),
        meta: { title: 'SAE报告' }
      },
      {
        path: 'deviation',
        name: 'Deviations',
        component: () => import('../views/Deviations.vue'),
        meta: { title: '方案偏离' }
      },
      {
        path: 'signal',
        name: 'Signals',
        component: () => import('../views/Signals.vue'),
        meta: { title: '信号挖掘' }
      },
      {
        path: 'compliance',
        name: 'Compliance',
        component: () => import('../views/Compliance.vue'),
        meta: { title: '合规质控' }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('../views/Knowledge.vue'),
        meta: { title: '知识库' }
      },
      {
        path: 'audit',
        name: 'Audit',
        component: () => import('../views/Audit.vue'),
        meta: { title: '审计日志' }
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