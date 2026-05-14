<template>
  <div class="profile-page">
    <div class="profile-card">
      <div class="profile-header">
        <div class="profile-avatar-wrapper">
          <UserAvatar :user="user" :size="80" />
        </div>
        <h1 class="profile-username">{{ user?.username || '未登录' }}</h1>
        <p class="profile-bio">{{ user?.bio || '这个人很懒，什么都没写' }}</p>
        <div v-if="isOtherUser" class="profile-follow">
          <FollowButton :user-id="userId" />
        </div>
      </div>

      <div class="profile-tabs">
        <button
          class="profile-tab"
          :class="{ active: activeTab === 'info' }"
          @click="activeTab = 'info'"
        >个人信息</button>
        <button
          class="profile-tab"
          :class="{ active: activeTab === 'articles' }"
          @click="activeTab = 'articles'"
        >我的文章</button>
        <button
          class="profile-tab"
          :class="{ active: activeTab === 'dynamics' }"
          @click="activeTab = 'dynamics'"
        >动态</button>
      </div>

      <div v-show="activeTab === 'info'" class="profile-info">
        <div class="info-item">
          <span class="info-label">邮箱</span>
          <span class="info-value">{{ user?.email || '-' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">注册时间</span>
          <span class="info-value">{{ formatDate(user?.created_at) }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">用户ID</span>
          <span class="info-value info-value-mono">{{ user?.id || '-' }}</span>
        </div>
      </div>

      <div v-show="activeTab === 'articles'" class="articles-section">
        <div v-if="myArticles.length === 0" class="empty-state">
          <p>还没有发布文章</p>
          <button class="btn-primary" @click="$router.push('/blogs/new')">写第一篇</button>
        </div>
        <div v-else class="articles-list">
          <article
            v-for="article in myArticles"
            :key="article.id"
            class="article-item"
            @click="$router.push(`/blogs/${article.id}`)"
          >
            <h3 class="article-title">{{ article.title }}</h3>
            <div class="article-meta">
              <span>{{ formatDate(article.created_at) }}</span>
              <span>{{ article.view_count }} 阅读</span>
              <span>{{ article.like_count }} 点赞</span>
            </div>
          </article>
        </div>
      </div>

      <div v-show="activeTab === 'dynamics'" class="dynamics-section">
        <DynamicFeed v-if="showDynamics" />
      </div>

      <div v-show="activeTab === 'info'" class="profile-actions">
        <button class="btn btn-outline" @click="handleLogout">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
            <polyline points="16 17 21 12 16 7"/>
            <line x1="21" y1="12" x2="9" y2="12"/>
          </svg>
          退出登录
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useBlogStore } from '@/stores/blogs'
import UserAvatar from '@/components/UserAvatar.vue'
import FollowButton from '@/components/FollowButton.vue'
import DynamicFeed from '@/components/DynamicFeed.vue'

const router = useRouter()
const authStore = useAuthStore()
const blogStore = useBlogStore()

const user = computed(() => authStore.user)
const activeTab = ref('info')
const showDynamics = ref(false)
const userId = computed(() => authStore.user?.id)
const isOtherUser = computed(() => false)
const myArticles = computed(() =>
  blogStore.blogs.filter(b => b.author_id === user.value?.id)
)

onMounted(() => {
  blogStore.fetchBlogs({ author_id: user.value?.id })
})

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function handleLogout() {
  authStore.logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: #F2F9F4;
  padding: 40px 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-card {
  width: 100%;
  max-width: 480px;
  background: #FFFFFF;
  border-radius: 24px;
  box-shadow: 0 12px 32px rgba(45,59,48,0.10), 0 4px 8px rgba(45,59,48,0.06);
  border: 1px solid #DDEEE5;
  overflow: hidden;
}

.profile-header {
  padding: 40px;
  text-align: center;
  background: linear-gradient(180deg, rgba(232,245,237,0.6) 0%, #FFFFFF 100%);
  border-bottom: 1px solid #DDEEE5;
}

.profile-avatar-wrapper {
  margin-bottom: 16px;
}

.profile-username {
  font-family: 'Lora', 'Noto Serif SC', Georgia, serif;
  font-size: 24px;
  font-weight: 600;
  color: #2D3B30;
  margin-bottom: 8px;
}

.profile-bio {
  font-size: 14px;
  color: #6B7D72;
  line-height: 1.6;
}

.profile-follow {
  margin-top: 16px;
}

.dynamics-section {
  padding: 24px 32px 32px;
}

.profile-info {
  padding: 24px 32px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #E8F0EB;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 14px;
  color: #6B7D72;
  font-weight: 500;
}

.info-value {
  font-size: 14px;
  color: #2D3B30;
  font-weight: 500;
}

.info-value-mono {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 12px;
  color: #6B7D72;
}

.profile-actions {
  padding: 24px 32px 32px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 600;
  font-family: 'Raleway', 'Noto Sans SC', -apple-system, sans-serif;
  transition: all 150ms ease;
  cursor: pointer;
  border: none;
  width: 100%;
}

.btn-outline {
  background: transparent;
  color: #5A9672;
  border: 1.5px solid #C8DCD2;
}

.btn-outline:hover {
  background: #E8F5ED;
  border-color: #97C9A8;
}

.profile-tabs {
  display: flex;
  border-bottom: 1px solid #E8F0EB;
  padding: 0 32px;
}
.profile-tab {
  padding: 16px 20px;
  font-size: 15px;
  font-weight: 500;
  color: #6B7D72;
  border: none;
  background: none;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 150ms ease;
}
.profile-tab:hover { color: #2D3B30; }
.profile-tab.active { color: #5A9672; border-bottom-color: #5A9672; }

.articles-section { padding: 24px 32px 32px; }
.empty-state { text-align: center; padding: 40px 0; color: #6B7D72; }
.empty-state p { margin-bottom: 16px; }
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  background: linear-gradient(135deg, #5A9672 0%, #7BAF8E 100%);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.articles-list { display: flex; flex-direction: column; gap: 12px; }
.article-item {
  padding: 16px;
  background: #F8FAF8;
  border-radius: 12px;
  cursor: pointer;
  transition: all 150ms ease;
}
.article-item:hover { background: #E8F5ED; }
.article-title { font-size: 15px; font-weight: 600; color: #2D3B30; margin-bottom: 8px; }
.article-meta { display: flex; gap: 16px; font-size: 13px; color: #6B7D72; }
</style>
