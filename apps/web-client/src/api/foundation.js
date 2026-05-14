import client from './index'

export const foundationApi = {
  checkIn() {
    return client.post('/api/foundation/checkin')
  },

  getStatus() {
    return client.get('/api/foundation/status')
  },

  getHistory() {
    return client.get('/api/foundation/history')
  },

  getAchievements() {
    return client.get('/api/foundation/achievements')
  },
}
