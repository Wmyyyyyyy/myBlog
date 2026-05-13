import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  function setUser(newUser) {
    user.value = newUser
    localStorage.setItem('user', JSON.stringify(newUser))
  }

  async function login(username, password) {
    const response = await authApi.login({ username, password })
    const { token: newToken, user: newUser } = response.data.data
    setToken(newToken)
    setUser(newUser)
    return response
  }

  async function register(username, email, password) {
    const response = await authApi.register({ username, email, password })
    return response
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const response = await authApi.me()
      setUser(response.data.data)
    } catch (error) {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  // Initialize: fetch user if token exists
  if (token.value) {
    fetchMe()
  }

  return {
    token,
    user,
    isLoggedIn,
    login,
    register,
    fetchMe,
    logout,
  }
})
