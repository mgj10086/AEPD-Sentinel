<template>
  <div id="app-root">
    <!-- 全局加载遮罩 -->
    <div v-if="store.globalLoading" class="global-loading-overlay">
      <div class="global-loading-content">
        <el-icon class="loading-spinner" :size="36"><Loading /></el-icon>
        <p>{{ store.globalLoadingText }}</p>
      </div>
    </div>

    <!-- 全局错误横幅 -->
    <el-alert
      v-if="store.globalError"
      :title="store.globalError.message"
      type="error"
      show-icon
      closable
      class="global-error-bar"
      @close="store.clearError()"
    >
      <template v-if="store.globalError.retry" #action>
        <el-button size="small" type="danger" @click="store.globalError.retry()">重试</el-button>
      </template>
    </el-alert>

    <router-view />
  </div>
</template>

<script setup>
import { Loading } from '@element-plus/icons-vue'
import { useAppStore } from './stores/app'

const store = useAppStore()
</script>

<style>
#app, #app-root {
  height: 100vh;
  position: relative;
}

.global-loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}
.global-loading-content {
  text-align: center;
  color: #409EFF;
}
.global-loading-content p {
  margin-top: 12px;
  font-size: 14px;
}
.loading-spinner {
  animation: rotating 1.4s linear infinite;
}
@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.global-error-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 9998;
  border-radius: 0;
}
</style>
