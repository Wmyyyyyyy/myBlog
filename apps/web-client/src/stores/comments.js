import { defineStore } from 'pinia'
import { ref } from 'vue'
import { commentApi } from '@/api/comments'

export const useCommentStore = defineStore('comments', () => {
  const comments = ref([])
  const isLoading = ref(false)

  async function fetchBlogComments(blogId, params = {}) {
    isLoading.value = true
    try {
      const response = await commentApi.getBlogComments(blogId, params)
      comments.value = response.data
    } finally {
      isLoading.value = false
    }
  }

  async function createComment(data) {
    const response = await commentApi.createComment(data)
    return response.data
  }

  async function deleteComment(commentId) {
    await commentApi.deleteComment(commentId)
    comments.value = comments.value.filter(c => c.id !== commentId)
  }

  return {
    comments,
    isLoading,
    fetchBlogComments,
    createComment,
    deleteComment,
  }
})
