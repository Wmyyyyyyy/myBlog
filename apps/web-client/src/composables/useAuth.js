import { useAuthStore } from '@/stores/auth'
import { storeToRefs } from 'pinia'

export function useAuth() {
  const authStore = useAuthStore()
  const { user, token, isLoggedIn } = storeToRefs(authStore)

  return {
    user,
    token,
    isLoggedIn,
    login: authStore.login,
    register: authStore.register,
    logout: authStore.logout,
    fetchMe: authStore.fetchMe,
  }
}
