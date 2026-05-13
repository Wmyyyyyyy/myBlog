<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-card-header">
        <div class="auth-logo">
          <div class="auth-logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span class="auth-logo-text">静心启慧</span>
        </div>
        <p class="auth-subtitle">探索智慧 · 静心成长</p>
      </div>
      <div class="auth-card-body">
        <form @submit.prevent="handleSubmit">
          <div class="form-group">
            <label class="form-label" for="username">用户名</label>
            <input
              id="username"
              v-model="form.username"
              type="text"
              class="form-input"
              placeholder="请输入用户名"
              autocomplete="username"
            >
          </div>
          <div class="form-group">
            <label class="form-label" for="password">密码</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              class="form-input"
              placeholder="请输入密码"
              autocomplete="current-password"
            >
          </div>
          <div class="form-group" style="display:flex;justify-content:space-between;align-items:center;">
            <label class="checkbox-label">
              <input type="checkbox" v-model="rememberMe">
              <span>记住我</span>
            </label>
            <a href="#" class="link-primary">忘记密码？</a>
          </div>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading">登录中...</span>
            <span v-else>登 录</span>
          </button>
        </form>
        <div class="auth-footer">
          还没有账号？<router-link to="/register" class="link-primary">立即注册</router-link>
        </div>
        <div class="divider-ornament">✦</div>
        <button class="btn btn-ghost" @click="$router.push('/blogs')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M12 8v4l3 3"/>
          </svg>
          先行浏览
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const formRef = ref(null)
const loading = ref(false)
const rememberMe = ref(false)

const form = reactive({
  username: '',
  password: '',
})

async function handleSubmit() {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/blogs')
  } catch (error) {
    // Error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: var(--color-background, #F2F9F4);
  position: relative;
  overflow: hidden;
}

.auth-page::before {
  content: '';
  position: absolute;
  top: -200px;
  right: -200px;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(90,150,114,0.08) 0%, transparent 70%);
  pointer-events: none;
}

.auth-page::after {
  content: '';
  position: absolute;
  bottom: -150px;
  left: -150px;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(151,201,168,0.10) 0%, transparent 70%);
  pointer-events: none;
}

.auth-card {
  width: 100%;
  max-width: 440px;
  background: #FFFFFF;
  border-radius: 24px;
  box-shadow: 0 24px 48px rgba(45,59,48,0.12), 0 8px 16px rgba(45,59,48,0.08);
  border: 1px solid #DDEEE5;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.auth-card-header {
  padding: 40px 40px 32px;
  text-align: center;
  border-bottom: 1px solid #DDEEE5;
  background: linear-gradient(180deg, rgba(232,245,237,0.6) 0%, transparent 100%);
}

.auth-logo {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.auth-logo-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #5A9672 0%, #97C9A8 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-logo-icon svg { width: 22px; height: 22px; color: white; }

.auth-logo-text {
  font-family: 'Lora', 'Noto Serif SC', Georgia, serif;
  font-size: 22px;
  font-weight: 700;
  color: #2D3B30;
  letter-spacing: 0.5px;
}

.auth-subtitle {
  font-size: 14px;
  color: #6B7D72;
  margin-top: 4px;
  font-weight: 400;
}

.auth-card-body {
  padding: 32px 40px 40px;
}

.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #2D3B30;
  margin-bottom: 6px;
  letter-spacing: 0.2px;
}

.form-input {
  width: 100%;
  padding: 11px 14px;
  border: 1.5px solid #C8DCD2;
  border-radius: 12px;
  font-size: 15px;
  font-family: 'Raleway', 'Noto Sans SC', -apple-system, sans-serif;
  color: #2D3B30;
  background: #FFFFFF;
  transition: border-color 150ms ease, box-shadow 150ms ease;
  outline: none;
}

.form-input:focus {
  border-color: #5A9672;
  box-shadow: 0 0 0 3px rgba(90,150,114,0.15);
}

.form-input::placeholder { color: #6B7D72; opacity: 0.7; }

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #6B7D72;
}

.checkbox-label input[type="checkbox"] {
  accent-color: #5A9672;
}

.link-primary {
  color: #5A9672;
  font-weight: 600;
  transition: color 150ms ease;
}

.link-primary:hover { color: #4A7D5F; }

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

.btn-primary {
  background: linear-gradient(135deg, #5A9672 0%, #7BAF8E 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(90,150,114,0.30);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(90,150,114,0.40);
}

.btn-primary:active { transform: translateY(0); }

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-ghost {
  background: transparent;
  color: #5A9672;
  border: 1.5px solid #C8DCD2;
}

.btn-ghost:hover {
  background: #E8F5ED;
  border-color: #97C9A8;
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: #6B7D72;
}

.divider-ornament {
  text-align: center;
  margin: 24px 0;
  color: #C8DCD2;
  font-size: 20px;
  letter-spacing: 8px;
}
</style>
