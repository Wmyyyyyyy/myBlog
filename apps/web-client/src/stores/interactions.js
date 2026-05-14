import { defineStore } from 'pinia'
import { ref } from 'vue'
import { interactionApi } from '@/api/interactions'

export const useInteractionStore = defineStore('interactions', () => {
  // Favorites
  const favorites = ref([])
  const favoriteStatus = ref({})

  async function toggleFavorite(blogId) {
    const status = favoriteStatus.value[blogId]
    if (status?.is_favorited) {
      await interactionApi.removeFavorite(blogId)
    } else {
      await interactionApi.addFavorite(blogId)
    }
    await checkFavoriteStatus(blogId)
  }

  async function checkFavoriteStatus(blogId) {
    const res = await interactionApi.getFavoriteStatus(blogId)
    favoriteStatus.value[blogId] = res.data
  }

  // Likes
  const likeStatus = ref({})

  async function toggleLike(blogId) {
    const status = likeStatus.value[blogId]
    if (status?.is_liked) {
      await interactionApi.removeLike(blogId)
    } else {
      await interactionApi.addLike(blogId)
    }
    await checkLikeStatus(blogId)
  }

  async function checkLikeStatus(blogId) {
    const res = await interactionApi.getLikeStatus(blogId)
    likeStatus.value[blogId] = res.data
  }

  // Follows
  const followStatus = ref({})

  async function toggleFollow(userId) {
    const status = followStatus.value[userId]
    if (status?.is_following) {
      await interactionApi.unfollow(userId)
    } else {
      await interactionApi.follow(userId)
    }
    await checkFollowStatus(userId)
  }

  async function checkFollowStatus(userId) {
    const res = await interactionApi.getFollowStatus(userId)
    followStatus.value[userId] = res.data
  }

  return {
    favorites,
    favoriteStatus,
    toggleFavorite,
    checkFavoriteStatus,
    likeStatus,
    toggleLike,
    checkLikeStatus,
    followStatus,
    toggleFollow,
    checkFollowStatus,
  }
})
