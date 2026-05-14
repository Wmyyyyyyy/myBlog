import client from './index'

export const blogApi = {
  createBlog(data) {
    return client.post('/api/blogs', data)
  },

  getBlogs(params) {
    return client.get('/api/blogs', { params })
  },

  getBlog(blogId) {
    return client.get(`/api/blogs/${blogId}`)
  },

  updateBlog(blogId, data) {
    return client.put(`/api/blogs/${blogId}`, data)
  },

  deleteBlog(blogId) {
    return client.delete(`/api/blogs/${blogId}`)
  },
}
