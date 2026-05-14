<template>
  <div class="blog-detail-page">
    <div v-if="blogStore.currentBlog" class="blog-detail">
      <header class="blog-header">
        <button class="btn btn-ghost back-btn" @click="$router.back()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          返回
        </button>
        <div class="blog-actions" v-if="isAuthor">
          <button class="btn btn-ghost" @click="$router.push(`/blogs/${blogId}/edit`)">编辑</button>
          <button class="btn btn-ghost delete-btn" @click="handleDelete">删除</button>
        </div>
      </header>

      <div class="blog-author" v-if="blog.author">
        <div class="author-avatar">
          <UserAvatar :user="blog.author" :size="40" />
        </div>
        <div class="author-info">
          <span class="author-name">{{ blog.author.username }}</span>
          <span class="author-date">{{ formatDate(blog.created_at) }}</span>
        </div>
      </div>

      <div class="blog-actions">
        <LikeButton :blog-id="blog.id" :initial-liked="liked" :initial-count="likeCount" />
        <FavoriteButton :blog-id="blog.id" :initial-favorited="favorited" />
      </div>

      <article class="blog-article">
        <h1 class="blog-title">{{ blog.title }}</h1>
        <div class="blog-meta">
          <span>{{ formatDate(blog.created_at) }}</span>
          <span>{{ blog.view_count }} 阅读</span>
        </div>
        <div class="blog-content" v-html="blog.content"></div>
      </article>

      <div class="blog-comments">
        <CommentSection :blog-id="blogId" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useBlogStore } from '@/stores/blogs'
import { useAuthStore } from '@/stores/auth'
import UserAvatar from '@/components/UserAvatar.vue'
import CommentSection from '@/components/CommentSection.vue'
import LikeButton from '@/components/LikeButton.vue'
import FavoriteButton from '@/components/FavoriteButton.vue'

const router = useRouter()
const route = useRoute()
const blogStore = useBlogStore()
const authStore = useAuthStore()

const blogId = route.params.id
const blog = computed(() => blogStore.currentBlog)
const isAuthor = computed(() =>
  blog.value?.author_id === authStore.user?.id
)

const liked = ref(false)
const favorited = ref(false)
const likeCount = ref(0)

function handleLike() {
  liked.value = !liked.value
  likeCount.value += liked.value ? 1 : -1
}

function handleFavorite() {
  favorited.value = !favorited.value
}

onMounted(() => {
  blogStore.fetchBlog(blogId)
})

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定要删除这篇博客吗？', '删除确认', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await blogStore.deleteBlog(blogId)
    ElMessage.success('删除成功')
    router.push('/blogs')
  } catch {
    // User cancelled
  }
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>

<style scoped>
.blog-detail-page { min-height: 100vh; background: #F2F9F4; }

.blog-detail {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px;
}

.blog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  color: #5A9672;
  background: transparent;
  border: 1px solid #C8DCD2;
  cursor: pointer;
}

.back-btn:hover { background: #E8F5ED; }

.blog-actions { display: flex; gap: 8px; }

.btn-ghost {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  color: #5A9672;
  background: transparent;
  border: 1px solid #C8DCD2;
  cursor: pointer;
}

.btn-ghost:hover { background: #E8F5ED; }

.delete-btn { color: #DC2626; border-color: #FECACA; }
.delete-btn:hover { background: #FEF2F2; }

.blog-article {
  background: #FFFFFF;
  border-radius: 24px;
  padding: 48px;
  box-shadow: 0 4px 12px rgba(45,59,48,0.08);
  border: 1px solid #DDEEE5;
}

.blog-title {
  font-family: 'Lora', 'Noto Serif SC', Georgia, serif;
  font-size: 36px;
  font-weight: 700;
  color: #2D3B30;
  margin-bottom: 16px;
  line-height: 1.3;
}

.blog-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: #6B7D72;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #E8F0EB;
}

.blog-content {
  font-size: 16px;
  line-height: 1.8;
  color: #2D3B30;
  white-space: pre-wrap;
}

.blog-author {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding: 16px;
  background: #F8FAF8;
  border-radius: 12px;
}
.author-info { display: flex; flex-direction: column; }
.author-name { font-size: 15px; font-weight: 600; color: #2D3B30; }
.author-date { font-size: 13px; color: #6B7D72; }

.blog-actions {
  display: flex;
  gap: 16px;
  margin-top: 16px;
}

.blog-comments { margin-top: 48px; }
</style>
