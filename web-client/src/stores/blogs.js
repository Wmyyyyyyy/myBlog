import { defineStore } from 'pinia'
import { ref } from 'vue'
import { blogApi } from '@/api/blogs'

export const useBlogStore = defineStore('blogs', () => {
  const blogs = ref([])
  const currentBlog = ref(null)
  const isLoading = ref(false)

  async function fetchBlogs(params = {}) {
    isLoading.value = true
    try {
      const response = await blogApi.getBlogs(params)
      blogs.value = response.data
    } finally {
      isLoading.value = false
    }
  }

  async function fetchBlog(blogId) {
    isLoading.value = true
    try {
      const response = await blogApi.getBlog(blogId)
      currentBlog.value = response.data
      return response.data
    } finally {
      isLoading.value = false
    }
  }

  async function createBlog(data) {
    const response = await blogApi.createBlog(data)
    return response.data
  }

  async function updateBlog(blogId, data) {
    const response = await blogApi.updateBlog(blogId, data)
    currentBlog.value = response.data
    return response.data
  }

  async function deleteBlog(blogId) {
    await blogApi.deleteBlog(blogId)
    blogs.value = blogs.value.filter((b) => b.id !== blogId)
  }

  return {
    blogs,
    currentBlog,
    isLoading,
    fetchBlogs,
    fetchBlog,
    createBlog,
    updateBlog,
    deleteBlog,
  }
})
