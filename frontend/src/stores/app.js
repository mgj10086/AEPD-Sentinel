import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const token = ref(localStorage.getItem('ae_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('ae_user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)

  // ---- 全局 loading/error 三态 ----
  const activeRequests = ref(0)
  const globalLoading = ref(false)
  const globalLoadingText = ref('')
  const globalError = ref(null) // { message, retry? }

  function startLoading(text = '加载中...') {
    activeRequests.value++
    globalLoading.value = true
    globalLoadingText.value = text
  }

  function stopLoading() {
    activeRequests.value = Math.max(0, activeRequests.value - 1)
    if (activeRequests.value === 0) {
      globalLoading.value = false
      globalLoadingText.value = ''
    }
  }

  function setError(err) {
    globalError.value = err
    globalLoading.value = false
    activeRequests.value = 0
  }

  function clearError() {
    globalError.value = null
  }

  // ----

  function login(userData, authToken) {
    token.value = authToken
    user.value = userData
    localStorage.setItem('ae_token', authToken)
    localStorage.setItem('ae_user', JSON.stringify(userData))
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('ae_token')
    localStorage.removeItem('ae_user')
  }

  return { token, user, isLoggedIn, login, logout,
           globalLoading, globalLoadingText, globalError,
           startLoading, stopLoading, setError, clearError }
})