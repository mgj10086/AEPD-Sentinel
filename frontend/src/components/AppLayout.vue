<template>
  <el-container class="app-layout">
    <el-aside width="220px" class="app-sidebar">
      <div class="logo">
        <el-icon :size="28"><Monitor /></el-icon>
        <span class="logo-text">AE Sentinel</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        background-color="#1a1a2e"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
      >
        <el-menu-item v-for="item in visibleRoutes" :key="item.path" :index="'/' + item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.meta?.title || item.path }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
          <!-- 通知铃铛 -->
          <el-popover
            v-model:visible="showNotifPanel"
            placement="bottom-end"
            :width="380"
            trigger="click"
            :popper-style="{ padding: '0' }"
          >
            <template #reference>
              <el-badge :value="unreadCount" :hidden="unreadCount === 0" class="notif-badge">
                <el-button text @click="fetchNotifications">
                  <el-icon :size="20"><Bell /></el-icon>
                </el-button>
              </el-badge>
            </template>
            <div class="notif-panel">
              <div class="notif-header">
                <span style="font-weight: 600">通知</span>
                <el-button text size="small" @click="markAllRead" :disabled="unreadCount === 0">全部已读</el-button>
              </div>
              <div class="notif-list" v-loading="notifLoading" :style="{ maxHeight: '400px', overflowY: 'auto' }">
                <div
                  v-for="n in notifications"
                  :key="n.notification_id"
                  class="notif-item"
                  :class="{ unread: !n.is_read }"
                  @click="handleNotifClick(n)"
                >
                  <div class="notif-title">
                    <el-tag :type="notifTypeMap[n.notification_type] || 'info'" size="small" effect="plain">
                      {{ n.title }}
                    </el-tag>
                    <span v-if="!n.is_read" class="notif-dot" />
                  </div>
                  <p class="notif-msg">{{ n.message }}</p>
                  <span class="notif-time">{{ n.created_at }}</span>
                </div>
                <el-empty v-if="!notifLoading && notifications.length === 0" description="暂无通知" :image-size="60" />
              </div>
            </div>
          </el-popover>

          <el-tag type="info" effect="plain" class="user-tag">
            <el-icon><User /></el-icon>
            {{ store.user?.name || '未知用户' }}
          </el-tag>
          <el-tag type="warning" effect="plain">
            {{ store.user?.role || '未知角色' }}
          </el-tag>
          <el-button type="danger" text @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
            退出
          </el-button>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { Bell } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'
import api from '../api'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

// ---- 角色菜单 ----
import {
  DataAnalysis, EditPen, Document, WarningFilled,
  TrendCharts, CircleCheckFilled, Collection, Clock, User
} from '@element-plus/icons-vue'

const roleIconMap = {
  dashboard: DataAnalysis,
  ae: EditPen,
  sae: Document,
  deviation: WarningFilled,
  signal: TrendCharts,
  compliance: CircleCheckFilled,
  knowledge: Collection,
  audit: Clock,
  users: User
}

const allChildRoutes = router.options.routes.find(r => r.path === '/')?.children || []

const visibleRoutes = computed(() => {
  const userRole = store.user?.role
  return allChildRoutes
    .filter(r => !r.meta?.roles || r.meta.roles.includes(userRole))
    .map(r => ({ ...r, icon: roleIconMap[r.path] || Document }))
})

// ----
const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta?.title || 'AE Sentinel')

// ---- 通知 ----
const unreadCount = ref(0)
const notifications = ref([])
const showNotifPanel = ref(false)
const notifLoading = ref(false)
let pollTimer = null

const notifTypeMap = {
  alert: 'danger',
  warning: 'warning',
  info: 'info',
  success: 'success'
}

async function fetchUnreadCount() {
  try {
    const res = await api.get('/api/notifications/unread-count')
    unreadCount.value = res.data?.count || 0
  } catch (e) {
    // silently fail for background polling
  }
}

async function fetchNotifications() {
  notifLoading.value = true
  try {
    const res = await api.get('/api/notifications/list', { params: { page: 1, page_size: 20 } })
    notifications.value = res.data?.items || []
  } catch (e) {
    console.error('获取通知失败', e)
  } finally {
    notifLoading.value = false
  }
}

async function markAllRead() {
  try {
    await api.put('/api/notifications/read-all')
    unreadCount.value = 0
    notifications.value.forEach(n => { n.is_read = 1 })
    ElMessage.success('已全部标记为已读')
  } catch (e) {
    console.error('标记已读失败', e)
  }
}

function handleNotifClick(n) {
  // 标记单条已读 + 跳转到相关页面
  if (!n.is_read) {
    api.put(`/api/notifications/${n.notification_id}/read`).catch(() => {})
    n.is_read = 1
    unreadCount.value = Math.max(0, unreadCount.value - 1)
  }
  // 根据 resource_type 跳转
  if (n.resource_type === 'deviation') {
    router.push('/deviation')
  } else if (n.resource_type === 'sae') {
    router.push('/sae')
  } else if (n.resource_type === 'ae') {
    router.push('/ae')
  } else if (n.resource_type === 'signal') {
    router.push('/signal')
  }
  showNotifPanel.value = false
}

function handleLogout() {
  store.logout()
  router.push('/login')
}

onMounted(() => {
  fetchUnreadCount()
  pollTimer = setInterval(fetchUnreadCount, 30000) // 每30秒轮询未读数
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.app-layout {
  height: 100vh;
}
.app-sidebar {
  background-color: #1a1a2e;
  overflow-y: auto;
  overflow-x: hidden;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #409EFF;
  border-bottom: 1px solid #2d2d4a;
}
.logo-text {
  font-size: 18px;
  font-weight: bold;
  color: #e0e6ed;
}
.app-sidebar .el-menu {
  border-right: none;
}
.app-header {
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 60px;
}
.header-left {
  display: flex;
  align-items: center;
}
.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #2B579A;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-tag {
  cursor: default;
}
.app-main {
  background: #f0f2f5;
  min-height: calc(100vh - 60px);
  padding: 20px;
}
/* 通知面板样式 */
:deep(.notif-badge .el-badge__content) {
  top: 12px;
  right: 6px;
}
.notif-panel {
  padding: 12px 0;
}
.notif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px 8px;
  border-bottom: 1px solid #ebeef5;
}
.notif-item {
  padding: 10px 16px;
  cursor: pointer;
  border-bottom: 1px solid #f2f2f2;
  transition: background 0.2s;
}
.notif-item:hover {
  background: #f5f7fa;
}
.notif-item.unread {
  background: #ecf5ff;
}
.notif-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.notif-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #409EFF;
  display: inline-block;
}
.notif-msg {
  margin: 2px 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.notif-time {
  font-size: 12px;
  color: #c0c4cc;
}
</style>