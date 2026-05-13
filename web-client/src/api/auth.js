import client from './index'

export const authApi = {
  register(data) {
    return client.post('/api/auth/register', data)
  },
  login(data) {
    return client.post('/api/auth/login', data)
  },
  logout() {
    return client.post('/api/auth/logout')
  },
  refreshToken(data) {
    return client.post('/api/auth/refresh', data)
  },
  me() {
    return client.get('/api/auth/me')
  },
}
