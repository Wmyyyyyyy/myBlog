import { defineStore } from 'pinia'
import { ref } from 'vue'
import { foundationApi } from '@/api/foundation'

export const useFoundationStore = defineStore('foundation', () => {
  const todayStatus = ref({ checked_in: false, streak: 0 })
  const history = ref({ dates: [], current_streak: 0, longest_streak: 0, total_checkins: 0 })
  const achievements = ref([])
  const isLoading = ref(false)

  async function fetchStatus() {
    const response = await foundationApi.getStatus()
    todayStatus.value = response.data
  }

  async function fetchHistory() {
    const response = await foundationApi.getHistory()
    history.value = response.data
  }

  async function fetchAchievements() {
    const response = await foundationApi.getAchievements()
    achievements.value = response.data
  }

  async function checkIn() {
    const response = await foundationApi.checkIn()
    await fetchStatus()
    await fetchHistory()
    await fetchAchievements()
    return response.data
  }

  async function fetchAll() {
    isLoading.value = true
    try {
      await Promise.all([fetchStatus(), fetchHistory(), fetchAchievements()])
    } finally {
      isLoading.value = false
    }
  }

  return {
    todayStatus,
    history,
    achievements,
    isLoading,
    fetchStatus,
    fetchHistory,
    fetchAchievements,
    checkIn,
    fetchAll,
  }
})
