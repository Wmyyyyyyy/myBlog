<template>
  <div class="logs-page">
    <div class="page-header">
      <h2>操作日志</h2>
    </div>

    <el-table :data="logs" v-loading="loading" stripe>
      <el-table-column prop="admin_username" label="管理员" width="120" />
      <el-table-column prop="action" label="操作" width="180">
        <template #default="{ row }">
          <el-tag>{{ row.action }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="target_type" label="对象类型" width="120" />
      <el-table-column prop="target_id" label="对象ID" width="200" show-overflow-tooltip />
      <el-table-column prop="detail" label="详情" show-overflow-tooltip />
      <el-table-column prop="ip_address" label="IP" width="130" />
      <el-table-column prop="created_at" label="时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString('zh-CN') }}
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="page"
      :page-size="50"
      :total="total"
      layout="total, prev, pager, next"
      @current-change="loadLogs"
      style="margin-top: 20px; justify-content: center"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import client from '@/api'

const logs = ref([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)

onMounted(() => loadLogs())

async function loadLogs() {
  loading.value = true
  try {
    const response = await client.get('/logs', { params: { skip: (page.value - 1) * 50, limit: 50 } })
    logs.value = response.data
    total.value = logs.value.length // 简化
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.logs-page { max-width: 1200px; }
.page-header { margin-bottom: 24px; }
.page-header h2 { font-size: 24px; }
</style>
