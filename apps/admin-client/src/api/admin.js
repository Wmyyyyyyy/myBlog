import axios from 'axios'

const adminClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: 30000,
})

// Add auth token
adminClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

export const adminApi = {
  // Dashboard
  getDashboardStats() {
    return adminClient.get('/api/admin/dashboard/stats')
  },

  // Users
  getUsers(params) {
    return adminClient.get('/api/admin/users', { params })
  },
  getUser(id) {
    return adminClient.get(`/api/admin/users/${id}`)
  },
  updateUser(id, data) {
    return adminClient.put(`/api/admin/users/${id}`, data)
  },
  banUser(id, data) {
    return adminClient.post(`/api/admin/users/${id}/ban`, data)
  },
  unbanUser(id) {
    return adminClient.post(`/api/admin/users/${id}/unban`)
  },
  resetPassword(id) {
    return adminClient.post(`/api/admin/users/${id}/reset-password`)
  },

  // Blogs
  getBlogs(params) {
    return adminClient.get('/api/admin/blogs', { params })
  },
  getBlog(id) {
    return adminClient.get(`/api/admin/blogs/${id}`)
  },
  updateBlog(id, data) {
    return adminClient.put(`/api/admin/blogs/${id}`, data)
  },
  deleteBlog(id) {
    return adminClient.delete(`/api/admin/blogs/${id}`)
  },
  unmarkBlogSensitive(id) {
    return adminClient.post(`/api/admin/blogs/${id}/unmark-sensitive`)
  },

  // Comments
  getComments(params) {
    return adminClient.get('/api/admin/comments', { params })
  },
  getComment(id) {
    return adminClient.get(`/api/admin/comments/${id}`)
  },
  updateComment(id, data) {
    return adminClient.put(`/api/admin/comments/${id}`, data)
  },
  deleteComment(id) {
    return adminClient.delete(`/api/admin/comments/${id}`)
  },
  unmarkCommentSensitive(id) {
    return adminClient.post(`/api/admin/comments/${id}/unmark-sensitive`)
  },

  // Sensitive Words
  getSensitiveWords(params) {
    return adminClient.get('/api/admin/sensitive-words', { params })
  },
  createSensitiveWord(data) {
    return adminClient.post('/api/admin/sensitive-words', data)
  },
  updateSensitiveWord(id, data) {
    return adminClient.put(`/api/admin/sensitive-words/${id}`, data)
  },
  deleteSensitiveWord(id) {
    return adminClient.delete(`/api/admin/sensitive-words/${id}`)
  },
  reloadSensitiveWords() {
    return adminClient.post('/api/admin/sensitive-words/reload')
  },

  // Security Logs
  getSecurityLogs(params) {
    return adminClient.get('/api/admin/logs/security', { params })
  },
  exportSecurityLogs(params) {
    return adminClient.get('/api/admin/logs/security/export', { params, responseType: 'blob' })
  },

  // IP Bans
  getIPBans(params) {
    return adminClient.get('/api/admin/ip-bans', { params })
  },
  createIPBan(data) {
    return adminClient.post('/api/admin/ip-bans', data)
  },
  deleteIPBan(ip) {
    return adminClient.delete(`/api/admin/ip-bans/${ip}`)
  },
  unbanAllIP(ip) {
    return adminClient.post(`/api/admin/ip-bans/${ip}/unban-all`)
  },

  // Operation Logs
  getOperationLogs(params) {
    return adminClient.get('/api/admin/logs/operation', { params })
  },

  // Login Logs
  getLoginLogs(params) {
    return adminClient.get('/api/admin/logs/login', { params })
  },
}
