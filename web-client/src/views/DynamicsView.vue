<template>
  <div class="dynamics-page">
    <nav class="dynamics-nav">
      <span class="nav-title">动态</span>
    </nav>

    <div class="dynamics-container">
      <!-- Publish box -->
      <div class="publish-box">
        <div class="publish-avatar">
          <UserAvatar :user="currentUser" :size="40" />
        </div>
        <div class="publish-input" @click="showPublishDialog = true">
          <span>分享你的想法...</span>
        </div>
      </div>

      <!-- Dynamic cards feed -->
      <div class="dynamics-feed">
        <div
          v-for="dynamic in dynamics"
          :key="dynamic.id"
          class="dynamic-card"
        >
          <div class="dynamic-header">
            <UserAvatar :user="dynamic.user" :size="40" />
            <div class="dynamic-author">
              <span class="author-name">{{ dynamic.user?.username }}</span>
              <span class="dynamic-time">{{ formatTime(dynamic.created_at) }}</span>
            </div>
          </div>
          <div class="dynamic-content">
            <p>{{ dynamic.content }}</p>
            <div v-if="dynamic.images?.length" class="dynamic-images">
              <img
                v-for="(img, i) in dynamic.images"
                :key="i"
                :src="img"
                class="dynamic-img"
              />
            </div>
          </div>
          <div class="dynamic-actions">
            <button class="action-btn" @click="handleLike(dynamic)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
              </svg>
              <span>{{ dynamic.like_count || '' }}</span>
            </button>
            <button class="action-btn" @click="handleComment(dynamic)">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              <span>{{ dynamic.comment_count || '' }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Publish dialog -->
    <el-dialog v-model="showPublishDialog" title="发布动态" width="500px">
      <textarea
        v-model="newContent"
        class="publish-textarea"
        placeholder="分享你的想法..."
        rows="4"
      ></textarea>
      <template #footer>
        <el-button @click="showPublishDialog = false">取消</el-button>
        <el-button type="primary" @click="handlePublish" :loading="publishing">发布</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import UserAvatar from '@/components/UserAvatar.vue'

const authStore = useAuthStore()
const currentUser = computed(() => authStore.user)
const showPublishDialog = ref(false)
const newContent = ref('')
const publishing = ref(false)

// Placeholder data for demo
const dynamics = ref([
  {
    id: 1,
    user: { id: 1, username: '林小夕', avatar: null },
    content: '今天天气真好呀！适合出去走走。顺便晒一下我养的绿萝，已经长得很茂盛了～',
    images: [],
    like_count: 24,
    comment_count: 5,
    created_at: new Date(Date.now() - 1800000).toISOString(),
  },
  {
    id: 2,
    user: { id: 2, username: '赵子涵', avatar: null },
    content: '分享最近读的一本书《活着》，余华老师的文字太有力量了，看完久久不能平静。',
    images: [],
    like_count: 18,
    comment_count: 12,
    created_at: new Date(Date.now() - 7200000).toISOString(),
  },
  {
    id: 3,
    user: { id: 3, username: '周明远', avatar: null },
    content: '周末爬山的照片，山顶的风景真美！',
    images: [
      'https://picsum.photos/400/300?random=1',
      'https://picsum.photos/400/300?random=2',
      'https://picsum.photos/400/300?random=3',
    ],
    like_count: 56,
    comment_count: 8,
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: 4,
    user: { id: 4, username: '陈雨萱', avatar: null },
    content: '新入手的咖啡机到了，准备开始学习拉花！有没有大神可以教教我～',
    images: [],
    like_count: 31,
    comment_count: 7,
    created_at: new Date(Date.now() - 172800000).toISOString(),
  },
])

onMounted(() => {
  // TODO: fetch dynamics from API when backend is ready
  // dynamicsStore.fetchDynamics()
})

function handlePublish() {
  if (!newContent.value.trim()) {
    ElMessage.warning('请输入内容')
    return
  }
  publishing.value = true
  // TODO: call API
  // await dynamicsStore.createDynamic({ content: newContent.value })
  setTimeout(() => {
    ElMessage.success('发布成功')
    showPublishDialog.value = false
    newContent.value = ''
    publishing.value = false
  }, 500)
}

function handleLike(dynamic) {
  // TODO: call API to toggle like
  if (dynamic.liked) {
    dynamic.like_count--
    dynamic.liked = false
  } else {
    dynamic.like_count++
    dynamic.liked = true
  }
}

function handleComment(dynamic) {
  // TODO: navigate to comment section or open dialog
  ElMessage.info('评论功能开发中...')
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
  if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.dynamics-page { min-height: 100vh; background: #F2F9F4; }

.dynamics-nav {
  position: sticky;
  top: 64px;
  z-index: 50;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #DDEEE5;
  padding: 12px 24px;
  text-align: center;
}
.nav-title {
  font-family: 'Lora', 'Noto Serif SC', Georgia, serif;
  font-size: 17px;
  font-weight: 700;
  color: #2D3B30;
}

.dynamics-container { max-width: 600px; margin: 0 auto; padding: 16px 16px 80px; }

.publish-box {
  display: flex;
  gap: 12px;
  align-items: center;
  background: #FFFFFF;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid #DDEEE5;
  box-shadow: 0 1px 3px rgba(45, 59, 48, 0.06);
}
.publish-avatar { flex-shrink: 0; }
.publish-input {
  flex: 1;
  padding: 10px 16px;
  background: #F2F9F4;
  border-radius: 100px;
  font-size: 14px;
  color: #6B7D72;
  cursor: pointer;
  transition: all 150ms ease;
}
.publish-input:hover { background: #E8F5ED; }

.dynamic-card {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 12px;
  border: 1px solid #DDEEE5;
  box-shadow: 0 1px 3px rgba(45, 59, 48, 0.04);
}
.dynamic-header {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
.dynamic-author { display: flex; flex-direction: column; }
.author-name { font-size: 14px; font-weight: 600; color: #2D3B30; }
.dynamic-time { font-size: 12px; color: #6B7D72; }
.dynamic-content p {
  font-size: 15px;
  line-height: 1.7;
  color: #2D3B30;
  white-space: pre-wrap;
  margin-bottom: 12px;
}
.dynamic-images { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; border-radius: 8px; overflow: hidden; }
.dynamic-img { width: 100%; aspect-ratio: 1; object-fit: cover; }
.dynamic-actions { display: flex; gap: 16px; margin-top: 12px; padding-top: 12px; border-top: 1px solid #F2F9F4; }
.action-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: #6B7D72;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 150ms ease;
}
.action-btn:hover { background: #E8F5ED; color: #5A9672; }

.publish-textarea {
  width: 100%;
  padding: 12px;
  border: 1.5px solid #C8DCD2;
  border-radius: 12px;
  font-size: 15px;
  font-family: 'Noto Sans SC', sans-serif;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
}
.publish-textarea:focus { border-color: #5A9672; }
</style>
