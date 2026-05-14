<template>
  <div class="review-page">
    <h2>内容审核</h2>
    <el-tabs v-model="activeTab">
      <el-tab-pane label="博客" name="blogs">
        <div v-for="blog in blogs" :key="blog.id" class="review-item">
          <div class="item-header">
            <span class="author">{{ blog.author_username }}</span>
            <span class="date">{{ new Date(blog.created_at).toLocaleString('zh-CN') }}</span>
          </div>
          <h3>{{ blog.title }}</h3>
          <div class="flagged-words">
            <el-tag v-for="word in blog.flagged_words" :key="word" type="warning">{{ word }}</el-tag>
          </div>
          <div class="item-actions">
            <el-button type="success" size="small" @click="handleApprove('blog', blog.id)">通过</el-button>
            <el-button type="danger" size="small" @click="handleReject('blog', blog.id)">删除</el-button>
          </div>
        </div>
        <el-empty v-if="blogs.length === 0" description="暂无待审核内容" />
      </el-tab-pane>
      <el-tab-pane label="评论" name="comments">
        <div v-for="comment in comments" :key="comment.id" class="review-item">
          <div class="item-header">
            <span class="author">{{ comment.author_username }}</span>
            <span class="date">{{ new Date(comment.created_at).toLocaleString('zh-CN') }}</span>
          </div>
          <p class="content">{{ comment.content }}</p>
          <div class="flagged-words">
            <el-tag v-for="word in comment.flagged_words" :key="word" type="warning">{{ word }}</el-tag>
          </div>
          <div class="item-actions">
            <el-button type="success" size="small" @click="handleApprove('comment', comment.id)">通过</el-button>
            <el-button type="danger" size="small" @click="handleReject('comment', comment.id)">删除</el-button>
          </div>
        </div>
        <el-empty v-if="comments.length === 0" description="暂无待审核内容" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/api'

const activeTab = ref('blogs')
const blogs = ref([])
const comments = ref([])

onMounted(() => loadData())

async function loadData() {
  try {
    const [blogRes, commentRes] = await Promise.all([
      client.get('/review/blogs'),
      client.get('/review/comments'),
    ])
    blogs.value = blogRes.data
    comments.value = commentRes.data
  } catch (error) {
    ElMessage.error('加载失败')
  }
}

async function handleApprove(type, id) {
  try {
    await client.post(`/review/${type}s/${id}`, { action: 'approve' })
    ElMessage.success('已通过')
    loadData()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

async function handleReject(type, id) {
  try {
    await ElMessageBox.confirm('确定删除该内容？', '确认', { type: 'warning' })
    await client.post(`/review/${type}s/${id}`, { action: 'reject' })
    ElMessage.success('已删除')
    loadData()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.review-page { max-width: 800px; }
.review-page h2 { font-size: 24px; margin-bottom: 24px; }
.review-item {
  background: #FFFFFF; border-radius: 12px; padding: 16px; margin-bottom: 16px;
  border: 1px solid #DDEEE5;
}
.item-header { display: flex; gap: 12px; margin-bottom: 8px; font-size: 13px; color: #6B7D72; }
.item-header .author { font-weight: 600; color: #2D3B30; }
.review-item h3 { font-size: 16px; margin-bottom: 8px; }
.review-item .content { color: #2D3B30; line-height: 1.6; margin-bottom: 12px; }
.flagged-words { display: flex; gap: 8px; margin-bottom: 12px; }
.item-actions { display: flex; gap: 8px; }
</style>
