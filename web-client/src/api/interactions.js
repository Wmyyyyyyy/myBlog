import client from './index'

export const interactionApi = {
  // Favorites
  addFavorite(blogId) {
    return client.post(`/api/interactions/favorites/${blogId}`)
  },
  removeFavorite(blogId) {
    return client.delete(`/api/interactions/favorites/${blogId}`)
  },
  getMyFavorites(params) {
    return client.get('/api/interactions/favorites/me', { params })
  },
  checkFavoriteStatus(blogId) {
    return client.get(`/api/interactions/favorites/${blogId}/status`)
  },

  // Likes
  addLike(blogId) {
    return client.post(`/api/interactions/likes/${blogId}`)
  },
  removeLike(blogId) {
    return client.delete(`/api/interactions/likes/${blogId}`)
  },
  checkLikeStatus(blogId) {
    return client.get(`/api/interactions/likes/${blogId}/status`)
  },

  // Follows
  follow(userId) {
    return client.post(`/api/interactions/follow/${userId}`)
  },
  unfollow(userId) {
    return client.delete(`/api/interactions/follow/${userId}`)
  },
  checkFollowStatus(userId) {
    return client.get(`/api/interactions/follow/${userId}/status`)
  },
  getFollowers(userId, params) {
    return client.get(`/api/interactions/followers/${userId}`, { params })
  },
  getFollowing(userId, params) {
    return client.get(`/api/interactions/following/${userId}`, { params })
  },

  // Dynamics
  getFeed(params) {
    return client.get('/api/dynamics/feed', { params })
  },
  getUserEvents(userId, params) {
    return client.get(`/api/dynamics/user/${userId}`, { params })
  },
}