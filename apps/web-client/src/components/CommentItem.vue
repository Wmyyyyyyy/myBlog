<template>
  <div class="comment-item" :style="{ marginLeft: level * 24 + 'px' }">
    <div class="comment-header">
      <el-avatar :size="32" class="comment-avatar">
        <el-icon><User /></el-icon>
      </el-avatar>
      <div class="comment-meta">
        <span class="comment-author">{{ comment.author_username }}</span>
        <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
      </div>
    </div>
    <div class="comment-content">{{ comment.content }}</div>
    <div class="comment-actions">
      <el-button text size="small" @click="showReplyInput = !showReplyInput">
        <el-icon><Comment /></el-icon>
        回复
      </el-button>
      <span class="action-count">
        <el-icon><Star /></el-icon>
        {{ comment.like_count }}
      </span>
      <el-button
        v-if="canDelete"
        text
        size="small"
        type="danger"
        @click="$emit('delete', comment.id)"
      >
        <el-icon><Delete /></el-icon>
        删除
      </el-button>
    </div>

    <!-- 回复输入框 -->
    <div v-if="showReplyInput" class="reply-input">
      <el-input
        v-model="replyContent"
        type="textarea"
        placeholder="写下你的回复..."
        :rows="2"
        size="small"
      />
      <div class="reply-actions">
        <el-button size="small" @click="cancelReply">取消</el-button>
        <el-button size="small" type="primary" @click="submitReply">发送</el-button>
      </div>
    </div>

    <!-- 子评论 -->
    <div v-if="comment.children && comment.children.length" class="comment-children">
      <CommentItem
        v-for="child in comment.children"
        :key="child.id"
        :comment="child"
        :blog-id="blogId"
        :level="level + 1"
        @reply="$emit('reply', $event)"
        @delete="$emit('delete', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElIcon, ElAvatar, ElButton } from 'element-plus'
import { User, Comment, Star, Delete } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const props = defineProps({
  comment: { type: Object, required: true },
  level: { type: Number, default: 0 },
  blogId: { type: String, required: true },
})

const emit = defineEmits(['reply', 'delete'])
const authStore = useAuthStore()
const showReplyInput = ref(false)
const replyContent = ref('')

const canDelete = computed(() => props.comment.author_id === authStore.user?.id)

function formatDate(dateStr) {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 30) return `${days}天前`
  return date.toLocaleDateString('zh-CN')
}

function submitReply() {
  if (!replyContent.value.trim()) return
  emit('reply', { parentId: props.comment.id, content: replyContent.value })
  showReplyInput.value = false
  replyContent.value = ''
}

function cancelReply() {
  showReplyInput.value = false
  replyContent.value = ''
}
</script>

<style scoped>
.comment-item {
  padding: 16px;
  background: #F9FAFA;
  border-radius: 12px;
  margin-bottom: 12px;
}
.comment-header {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
}
.comment-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.comment-author {
  font-weight: 600;
  color: #2D3B30;
  font-size: 14px;
}
.comment-time {
  color: #6B7D72;
  font-size: 12px;
}
.comment-content {
  color: #2D3B30;
  line-height: 1.6;
  margin-bottom: 8px;
  padding-left: 40px;
}
.comment-actions {
  display: flex;
  gap: 16px;
  font-size: 13px;
  color: #6B7D72;
  padding-left: 40px;
  align-items: center;
}
.action-count {
  display: flex;
  align-items: center;
  gap: 4px;
}
.comment-children {
  margin-top: 12px;
  padding-left: 24px;
}
.reply-input {
  margin-top: 8px;
  padding-left: 40px;
}
.reply-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
