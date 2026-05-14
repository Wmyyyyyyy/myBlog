<template>
  <div class="editor-page">
    <div class="editor-header">
      <button class="btn btn-ghost" @click="$router.back()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        返回
      </button>
      <div class="header-actions">
        <button class="btn btn-outline" @click="saveDraft">保存草稿</button>
        <button class="btn btn-primary" @click="handleSubmit" :disabled="loading">
          {{ loading ? '发布中...' : '发布' }}
        </button>
      </div>
    </div>

    <div class="editor-container">
      <div class="metadata-card">
        <div class="form-row">
          <div class="form-group">
            <label>分类</label>
            <select v-model="form.category" class="form-select">
              <option value="">请选择分类</option>
              <option value="心灵成长">心灵成长</option>
              <option value="读书笔记">读书笔记</option>
              <option value="百日筑基">百日筑基</option>
              <option value="禅意生活">禅意生活</option>
              <option value="诗词鉴赏">诗词鉴赏</option>
              <option value="经典导读">经典导读</option>
            </select>
          </div>
          <div class="form-group">
            <label>标签</label>
            <input v-model="form.tags" type="text" class="form-input" placeholder="用逗号分隔，如: 冥想,正念" />
          </div>
        </div>
        <div class="form-group">
          <label>封面图片 URL（可选）</label>
          <input v-model="form.cover_image" type="text" class="form-input" placeholder="https://..." />
        </div>
      </div>

      <div class="editor-card">
        <input
          v-model="form.title"
          type="text"
          class="title-input"
          placeholder="在这里写下你的文章标题..."
          maxlength="200"
        >
        <textarea
          v-model="form.content"
          class="content-textarea"
          placeholder="开始写作吧..."
        ></textarea>
      </div>

      <div class="editor-footer">
        <span class="word-count">{{ form.content.length }} 字</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useBlogStore } from '@/stores/blogs'

const router = useRouter()
const route = useRoute()
const blogStore = useBlogStore()

const isEdit = route.name === 'BlogEdit'
const loading = ref(false)
const blogId = route.params.id

const form = reactive({
  title: '',
  content: '',
  excerpt: '',
  category: '',
  tags: '',
  cover_image: '',
})

onMounted(async () => {
  if (isEdit && blogId) {
    const blog = await blogStore.fetchBlog(blogId)
    form.title = blog.title
    form.content = blog.content
    form.excerpt = blog.excerpt || ''
    form.category = blog.category || ''
    form.tags = blog.tags || ''
    form.cover_image = blog.cover_image || ''
  }
})

async function handleSubmit() {
  if (!form.title.trim()) {
    ElMessage.warning('请输入标题')
    return
  }
  if (!form.content.trim()) {
    ElMessage.warning('请输入内容')
    return
  }

  loading.value = true
  try {
    if (isEdit) {
      await blogStore.updateBlog(blogId, form)
      ElMessage.success('更新成功')
    } else {
      await blogStore.createBlog(form)
      ElMessage.success('发布成功')
    }
    router.push('/blogs')
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}

function saveDraft() {
  localStorage.setItem('blog_draft', JSON.stringify(form))
  ElMessage.success('草稿已保存')
}
</script>

<style scoped>
.editor-page { min-height: 100vh; background: #F2F9F4; }

.editor-header {
  position: sticky;
  top: 64px;
  z-index: 50;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid #DDEEE5;
}
.header-actions { display: flex; gap: 12px; }

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 150ms ease;
}
.btn-primary {
  background: linear-gradient(135deg, #5A9672 0%, #7BAF8E 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 12px rgba(90,150,114,0.30);
}
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(90,150,114,0.40); }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-outline { background: transparent; color: #5A9672; border: 1.5px solid #C8DCD2; }
.btn-outline:hover { background: #E8F5ED; }
.btn-ghost { background: transparent; color: #6B7D72; border: none; }
.btn-ghost:hover { color: #2D3B30; }

.editor-container { max-width: 800px; margin: 0 auto; padding: 24px; }

.metadata-card {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 20px 24px;
  margin-bottom: 16px;
  border: 1px solid #DDEEE5;
}
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 13px; font-weight: 600; color: #2D3B30; }
.form-input, .form-select {
  padding: 10px 14px;
  border: 1.5px solid #C8DCD2;
  border-radius: 8px;
  font-size: 14px;
  font-family: 'Noto Sans SC', sans-serif;
  color: #2D3B30;
  background: #FFFFFF;
  outline: none;
  transition: border-color 150ms ease;
}
.form-input:focus, .form-select:focus { border-color: #5A9672; }
.form-input::placeholder { color: #6B7D72; opacity: 0.7; }

.editor-card {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 32px;
  border: 1px solid #DDEEE5;
}
.title-input {
  width: 100%;
  padding: 8px 0 16px;
  border: none;
  font-size: 28px;
  font-family: 'Lora', 'Noto Serif SC', Georgia, serif;
  font-weight: 700;
  color: #2D3B30;
  background: transparent;
  outline: none;
}
.title-input::placeholder { color: #97C9A8; }
.title-input::after { content: ''; display: block; height: 1px; background: #E8F0EB; margin-top: 16px; }

.content-textarea {
  width: 100%;
  min-height: 400px;
  padding: 16px 0;
  border: none;
  font-size: 16px;
  line-height: 1.9;
  color: #2D3B30;
  background: transparent;
  outline: none;
  resize: none;
  font-family: 'Noto Sans SC', sans-serif;
}
.content-textarea::placeholder { color: #C4D4C8; }

.editor-footer {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0;
}
.word-count { font-size: 13px; color: #6B7D72; }
</style>
