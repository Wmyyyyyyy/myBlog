import client from './index'

export const interactionApi = {
  // Favorites
  addFavorite(blogId) {
    return client.post(`/api/interactions/favorites/${blogId}`)
  },
  removeFavorite(blogId) {
    return client.delete(`/api/interactions/favorites/${blogId}`)
  },
  getFavoriteStatus(blogId) {
    return client.get(`/api/interactions/favorites/${blogId}/status`)
  },
  getMyFavorites(params) {
    return client.get('/api/interactions/favorites', { params })
  },

  // Likes
  addLike(blogId) {
    return client.post(`/api/interactions/likes/${blogId}`)
  },
  removeLike(blogId) {
    return client.delete(`/api/interactions/likes/${blogId}`)
  },
  getLikeStatus(blogId) {
    return client.get(`/api/interactions/likes/${blogId}/status`)
  },

  // Follows
  follow(userId) {
    return client.post(`/api/interactions/follows/${userId}`)
  },
  unfollow(userId) {
    return client.delete(`/api/interactions/follows/${userId}`)
  },
  getFollowStatus(userId) {
    return client.get(`/api/interactions/follows/${userId}/status`)
  },
  getFollowers(userId, params) {
    return client.get(`/api/interactions/followers/${userId}`, { params })
  },
  getFollowing(userId, params) {
    return client.get(`/api/interactions/following/${userId}`, { params })
  },
}
