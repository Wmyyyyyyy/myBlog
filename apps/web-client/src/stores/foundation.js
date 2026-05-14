import { defineStore } from 'pinia'
import { ref } from 'vue'
import { foundationApi } from '@/api/foundation'

export const useFoundationStore = defineStore('foundation', () => {
  const status = ref({
    today_checked_in: false,
    current_streak: 0,
    longest_streak: 0,
    message: ''
  })
  const history = ref([])
  const historyTotal = ref(0)
  const isLoading = ref(false)

  async function fetchStatus() {
    const res = await foundationApi.getStatus()
    status.value = res.data
  }

  async function checkIn() {
    const res = await foundationApi.checkIn()
    status.value = res.data
    await fetchHistory()
    return res.data
  }

  async function fetchHistory(params = {}) {
    isLoading.value = true
    try {
      const res = await foundationApi.getHistory(params)
      history.value = res.data.records
      historyTotal.value = res.data.total
    } finally {
      isLoading.value = false
    }
  }

  return {
    status,
    history,
    historyTotal,
    isLoading,
    fetchStatus,
    checkIn,
    fetchHistory,
  }
})
