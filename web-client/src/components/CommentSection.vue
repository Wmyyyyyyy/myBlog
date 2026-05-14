<template>
  <div class="comment-section">
    <h3 class="comment-title">评论 {{ totalCount }}</h3>

    <!-- 发布评论 -->
    <div class="comment-form">
      <el-input
        v-model="newComment"
        type="textarea"
        placeholder="写下你的评论..."
        :rows="3"
        class="comment-input"
      />
      <el-button type="primary" @click="handleSubmit" :disabled="!newComment.trim()">
        发布
      </el-button>
    </div>

    <!-- 排序切换 -->
    <div class="comment-tabs">
      <el-radio-group v-model="sort" @change="switchSort">
        <el-radio-button value="latest">最新</el-radio-button>
        <el-radio-button value="hottest">最热</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 评论列表 -->
    <div class="comment-list">
      <CommentItem
        v-for="comment in commentStore.comments"
        :key="comment.id"
        :comment="comment"
        :blog-id="blogId"
        @reply="handleReply"
        @delete="handleDelete"
      />
    </div>

    <!-- 空状态 -->
    <el-empty v-if="!commentStore.isLoading && commentStore.comments.length === 0" description="暂无评论" />
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useCommentStore } from '@/stores/comments'
import { useAuthStore } from '@/stores/auth'
import CommentItem from './CommentItem.vue'

const props = defineProps({
  blogId: { type: String, required: true }
})

const commentStore = useCommentStore()
const authStore = useAuthStore()
const newComment = ref('')
const sort = ref('latest')

const totalCount = computed(() => commentStore.comments.length)

function switchSort(newSort) {
  commentStore.fetchBlogComments(props.blogId, { sort: newSort })
}

async function handleSubmit() {
  if (!newComment.value.trim()) return
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  try {
    await commentStore.createComment({
      blog_id: props.blogId,
      content: newComment.value,
    })
    newComment.value = ''
    ElMessage.success('评论成功')
    commentStore.fetchBlogComments(props.blogId, { sort: sort.value })
  } catch (error) {
    ElMessage.error('评论失败')
  }
}

function handleReply({ parentId, content }) {
  if (!authStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    return
  }
  commentStore.createComment({
    blog_id: props.blogId,
    content: content,
    parent_id: parentId,
  }).then(() => {
    ElMessage.success('回复成功')
    commentStore.fetchBlogComments(props.blogId, { sort: sort.value })
  }).catch(() => {
    ElMessage.error('回复失败')
  })
}

async function handleDelete(commentId) {
  try {
    await commentStore.deleteComment(commentId)
    ElMessage.success('删除成功')
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

// 初始加载
commentStore.fetchBlogComments(props.blogId)
</script>

<style scoped>
.comment-section {
  padding: 24px;
  background: #FFFFFF;
  border-radius: 16px;
}
.comment-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #2D3B30;
}
.comment-form {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  align-items: flex-start;
}
.comment-input {
  flex: 1;
}
.comment-tabs {
  margin-bottom: 16px;
}
.comment-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
