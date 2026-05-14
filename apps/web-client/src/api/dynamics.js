import client from './index'

export const dynamicsApi = {
  getFeed(params) {
    return client.get('/api/dynamics/feed', { params })
  },
  getUserEvents(userId, params) {
    return client.get(`/api/dynamics/user/${userId}`, { params })
  },
}
