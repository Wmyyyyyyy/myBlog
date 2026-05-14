<template>
  <div class="users-page">
    <div class="page-header">
      <h2>用户管理</h2>
      <div class="filters">
        <el-input v-model="search" placeholder="搜索用户名/邮箱" clearable style="width: 200px" />
        <el-select v-model="isActive" placeholder="状态" clearable style="width: 120px">
          <el-option label="正常" :value="true" />
          <el-option label="已封禁" :value="false" />
        </el-select>
      </div>
    </div>

    <el-table :data="users" v-loading="loading" stripe>
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="blog_count" label="博客数" width="100" />
      <el-table-column prop="comment_count" label="评论数" width="100" />
      <el-table-column prop="is_active" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '正常' : '已封禁' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_admin" label="角色" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.is_admin" type="warning">管理员</el-tag>
          <span v-else>普通用户</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button v-if="row.is_active && !row.is_admin" type="danger" size="small" @click="handleBan(row)">
            封禁
          </el-button>
          <el-button v-else-if="!row.is_active" type="success" size="small" @click="handleUnban(row)">
            解封
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="20"
      :total="total"
      layout="total, prev, pager, next"
      @current-change="loadUsers"
      style="margin-top: 20px; justify-content: center"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/api'

const users = ref([])
const loading = ref(false)
const search = ref('')
const isActive = ref(null)
const page = ref(1)
const total = ref(0)

onMounted(() => loadUsers())

async function loadUsers() {
  loading.value = true
  try {
    const params = { skip: (page.value - 1) * 20, limit: 20 }
    if (search.value) params.search = search.value
    if (isActive.value !== null) params.is_active = isActive.value
    const response = await client.get('/users', { params })
    users.value = response.data
    total.value = users.value.length // 简化，实际需要 total count
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

async function handleBan(user) {
  try {
    await ElMessageBox.confirm(`确定封禁用户 ${user.username}？`, '确认', { type: 'warning' })
    await client.post('/users/ban', { user_id: user.id })
    ElMessage.success('已封禁')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('操作失败')
  }
}

async function handleUnban(user) {
  try {
    await client.post('/users/unban', { user_id: user.id })
    ElMessage.success('已解封')
    loadUsers()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.users-page { max-width: 1000px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { font-size: 24px; }
.filters { display: flex; gap: 12px; }
</style>
