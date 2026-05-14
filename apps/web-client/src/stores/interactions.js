import { defineStore } from 'pinia'
import { ref } from 'vue'
import { interactionApi } from '@/api/interactions'

export const useInteractionStore = defineStore('interactions', () => {
  // State
  const feed = ref([])
  const isLoading = ref(false)

  // Favorites
  async function toggleFavorite(blogId, currentStatus) {
    if (currentStatus) {
      await interactionApi.removeFavorite(blogId)
    } else {
      await interactionApi.addFavorite(blogId)
    }
  }

  // Likes
  async function toggleLike(blogId, currentStatus) {
    if (currentStatus) {
      await interactionApi.removeLike(blogId)
    } else {
      await interactionApi.addLike(blogId)
    }
  }

  // Follows
  async function toggleFollow(userId, currentStatus) {
    if (currentStatus) {
      await interactionApi.unfollow(userId)
    } else {
      await interactionApi.follow(userId)
    }
  }

  // Dynamics
  async function fetchFeed(params = {}) {
    isLoading.value = true
    try {
      const response = await interactionApi.getFeed(params)
      feed.value = response.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchUserEvents(userId, params = {}) {
    const response = await interactionApi.getUserEvents(userId, params)
    return response.data
  }

  return {
    feed,
    isLoading,
    toggleFavorite,
    toggleLike,
    toggleFollow,
    fetchFeed,
    fetchUserEvents,
  }
})