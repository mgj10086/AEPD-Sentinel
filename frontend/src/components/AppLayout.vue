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
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        <el-menu-item index="/ae">
          <el-icon><EditPen /></el-icon>
          <span>AE编码</span>
        </el-menu-item>
        <el-menu-item index="/sae">
          <el-icon><Document /></el-icon>
          <span>SAE报告</span>
        </el-menu-item>
        <el-menu-item index="/deviation">
          <el-icon><WarningFilled /></el-icon>
          <span>方案偏离</span>
        </el-menu-item>
        <el-menu-item index="/signal">
          <el-icon><TrendCharts /></el-icon>
          <span>信号挖掘</span>
        </el-menu-item>
        <el-menu-item index="/compliance">
          <el-icon><CircleCheckFilled /></el-icon>
          <span>合规质控</span>
        </el-menu-item>
        <el-menu-item index="/knowledge">
          <el-icon><Collection /></el-icon>
          <span>知识库</span>
        </el-menu-item>
        <el-menu-item index="/audit">
          <el-icon><Clock /></el-icon>
          <span>审计日志</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <span class="page-title">{{ pageTitle }}</span>
        </div>
        <div class="header-right">
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
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '../stores/app'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta?.title || 'AE Sentinel')

function handleLogout() {
  store.logout()
  router.push('/login')
}
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
</style>