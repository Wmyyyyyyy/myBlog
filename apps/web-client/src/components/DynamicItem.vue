<template>
  <div class="dynamic-item">
    <div class="user-info">
      <img :src="event.user_avatar || defaultAvatar" class="avatar" />
      <span class="username">{{ event.user_username }}</span>
    </div>
    <div class="content">
      {{ actionText }} {{ targetText }}
    </div>
    <div class="time">{{ formatTime(event.created_at) }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  event: { type: Object, required: true }
})

const defaultAvatar = '/default-avatar.png'

const actionText = computed(() => {
  const map = {
    blog_post: '发布了博客',
    like_blog: '点赞了',
    favorite_blog: '收藏了',
    follow_user: '关注了',
    follow: '关注了',
    checkin: '完成了打卡'
  }
  return map[props.event.event_type] || props.event.event_type
})

const targetText = computed(() => {
  if (props.event.target_title) {
    return `"${props.event.target_title}"`
  }
  return ''
})

function formatTime(dateStr) {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff/60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff/3600000)}小时前`
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.dynamic-item { padding: 16px; background: #f9fafa; border-radius: 12px; margin-bottom: 12px; }
.user-info { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.avatar { width: 32px; height: 32px; border-radius: 50%; }
.username { font-weight: 600; color: #2d3b30; }
.content { color: #2d3b30; line-height: 1.5; }
.time { color: #6b7d72; font-size: 12px; margin-top: 8px; }
</style>
