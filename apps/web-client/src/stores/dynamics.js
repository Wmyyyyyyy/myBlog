import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dynamicsApi } from '@/api/dynamics'

export const useDynamicsStore = defineStore('dynamics', () => {
  const events = ref([])
  const nextCursor = ref(null)
  const isLoading = ref(false)

  async function fetchFeed(reset = false) {
    if (reset) {
      events.value = []
      nextCursor.value = null
    }
    isLoading.value = true
    try {
      const params = {}
      if (nextCursor.value) {
        params.cursor = JSON.stringify(nextCursor.value)
      }
      const res = await dynamicsApi.getFeed(params)
      events.value.push(...res.data.events)
      nextCursor.value = res.data.next_cursor
    } finally {
      isLoading.value = false
    }
  }

  return {
    events,
    nextCursor,
    isLoading,
    fetchFeed,
  }
})
