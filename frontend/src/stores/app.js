import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAppStore = defineStore('app', () => {
  const token = ref(localStorage.getItem('ae_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('ae_user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)

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

  return { token, user, isLoggedIn, login, logout }
})