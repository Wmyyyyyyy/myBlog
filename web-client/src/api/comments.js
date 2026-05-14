import client from './index'

export const commentApi = {
  createComment(data) {
    return client.post('/api/comments', data)
  },

  getBlogComments(blogId, params) {
    return client.get(`/api/comments/blog/${blogId}`, { params })
  },

  getCommentReplies(commentId, params) {
    return client.get(`/api/comments/${commentId}/replies`, { params })
  },

  deleteComment(commentId) {
    return client.delete(`/api/comments/${commentId}`)
  },
}
