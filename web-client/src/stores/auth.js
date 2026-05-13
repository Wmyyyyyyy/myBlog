import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const isLoading = ref(false)

  const isLoggedIn = computed(() => !!token.value)

  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('access_token', newToken)
  }

  function setRefreshToken(newRefreshToken) {
    refreshToken.value = newRefreshToken
    localStorage.setItem('refresh_token', newRefreshToken)
  }

  function setUser(newUser) {
    user.value = newUser
    localStorage.setItem('user', JSON.stringify(newUser))
  }

  async function login(username, password) {
    const response = await authApi.login({ username, password })
    const { access_token, refresh_token } = response.data
    setToken(access_token)
    setRefreshToken(refresh_token)
    await fetchMe()
    return response
  }

  async function register(username, email, password) {
    await authApi.register({ username, email, password })
    // Auto login after registration
    await login(username, password)
  }

  async function fetchMe() {
    if (!token.value || isLoading.value) return
    isLoading.value = true
    try {
      const response = await authApi.me()
      setUser(response.data)
    } catch (error) {
      if (error.response?.status === 401) {
        // Token invalid, try refresh
        const refreshed = await refreshAccessToken()
        if (refreshed) {
          const retryResponse = await authApi.me()
          setUser(retryResponse.data)
        } else {
          logout()
        }
      } else {
        logout()
      }
    } finally {
      isLoading.value = false
    }
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) return false
    try {
      const response = await authApi.refreshToken({ refresh_token: refreshToken.value })
      const { access_token, refresh_token: newRefreshToken } = response.data
      setToken(access_token)
      setRefreshToken(newRefreshToken)
      return true
    } catch {
      logout()
      return false
    }
  }

  function logout() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  // Initialize: fetch user if token exists
  if (token.value) {
    fetchMe()
  }

  return {
    token,
    refreshToken,
    user,
    isLoggedIn,
    isLoading,
    login,
    register,
    fetchMe,
    refreshAccessToken,
    logout,
  }
})
