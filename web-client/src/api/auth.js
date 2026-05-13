import client from './index'

export const authApi = {
  register(data) {
    return client.post('/api/auth/register', data)
  },

  login(data) {
    // OAuth2PasswordRequestForm expects form data, not JSON
    const formData = new URLSearchParams()
    formData.append('username', data.username)
    formData.append('password', data.password)
    return client.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
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
