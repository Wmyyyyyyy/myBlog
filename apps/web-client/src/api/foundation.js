import client from './index'

export const foundationApi = {
  checkIn() {
    return client.post('/api/foundation/checkin')
  },

  getStatus() {
    return client.get('/api/foundation/status')
  },

  getHistory(params) {
    return client.get('/api/foundation/history', { params })
  },

  getAchievements() {
    return client.get('/api/foundation/achievements')
  },
}
