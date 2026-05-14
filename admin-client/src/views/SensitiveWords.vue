<template>
  <div class="sensitive-words-page">
    <div class="page-header">
      <h2>敏感词管理</h2>
      <div class="actions">
        <el-button type="primary" @click="showAddDialog = true">添加敏感词</el-button>
        <el-button @click="handleReload">重新加载过滤器</el-button>
      </div>
    </div>

    <el-table :data="words" v-loading="loading" stripe>
      <el-table-column prop="word" label="敏感词" />
      <el-table-column prop="action" label="动作" width="120">
        <template #default="{ row }">
          <el-tag :type="row.action === 'block' ? 'danger' : row.action === 'replace' ? 'warning' : 'info'">
            {{ row.action === 'block' ? '拦截' : row.action === 'replace' ? '替换' : '警告' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString('zh-CN') }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加/编辑对话框 -->
    <el-dialog v-model="showAddDialog" :title="editingWord ? '编辑敏感词' : '添加敏感词'" width="400px">
      <el-form ref="formRef" :model="form" label-width="80px">
        <el-form-item label="敏感词">
          <el-input v-model="form.word" placeholder="请输入敏感词" />
        </el-form-item>
        <el-form-item label="动作">
          <el-select v-model="form.action" style="width: 100%">
            <el-option label="拦截 (block)" value="block" />
            <el-option label="替换 (replace)" value="replace" />
            <el-option label="警告 (warn)" value="warn" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import client from '@/api'

const words = ref([])
const loading = ref(false)
const showAddDialog = ref(false)
const editingWord = ref(null)
const formRef = ref(null)

const form = reactive({ word: '', action: 'warn' })

onMounted(() => loadWords())

async function loadWords() {
  loading.value = true
  try {
    const response = await client.get('/sensitive-words')
    words.value = response.data
  } catch (error) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

function handleEdit(word) {
  editingWord.value = word
  form.word = word.word
  form.action = word.action
  showAddDialog.value = true
}

async function handleSave() {
  try {
    if (editingWord.value) {
      await client.put(`/sensitive-words/${editingWord.value.id}`, form)
      ElMessage.success('更新成功')
    } else {
      await client.post('/sensitive-words', form)
      ElMessage.success('添加成功')
    }
    showAddDialog.value = false
    editingWord.value = null
    form.word = ''
    form.action = 'warn'
    loadWords()
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

async function handleDelete(word) {
  try {
    await ElMessageBox.confirm(`确定删除敏感词 "${word.word}"？`, '确认', { type: 'warning' })
    await client.delete(`/sensitive-words/${word.id}`)
    ElMessage.success('删除成功')
    loadWords()
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('删除失败')
  }
}

async function handleReload() {
  try {
    await client.post('/sensitive-words/reload')
    ElMessage.success('过滤器已重新加载')
  } catch (error) {
    ElMessage.error('重新加载失败')
  }
}
</script>

<style scoped>
.sensitive-words-page { max-width: 1000px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { font-size: 24px; }
.actions { display: flex; gap: 12px; }
</style>
