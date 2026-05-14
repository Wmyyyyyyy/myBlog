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
        <p class="auth-subtitle">开启智慧之旅</p>
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
              placeholder="3-50个字符"
              autocomplete="username"
            >
          </div>
          <div class="form-group">
            <label class="form-label" for="email">邮箱</label>
            <input
              id="email"
              v-model="form.email"
              type="email"
              class="form-input"
              placeholder="请输入邮箱"
              autocomplete="email"
            >
          </div>
          <div class="form-group">
            <label class="form-label" for="password">密码</label>
            <input
              id="password"
              v-model="form.password"
              type="password"
              class="form-input"
              placeholder="至少8个字符"
              autocomplete="new-password"
            >
          </div>
          <div class="form-group">
            <label class="form-label" for="confirmPassword">确认密码</label>
            <input
              id="confirmPassword"
              v-model="form.confirmPassword"
              type="password"
              class="form-input"
              placeholder="请再次输入密码"
              autocomplete="new-password"
            >
          </div>
          <button type="submit" class="btn btn-primary" :disabled="loading">
            <span v-if="loading">注册中...</span>
            <span v-else>注 册</span>
          </button>
        </form>
        <div class="auth-footer">
          已有账号？<router-link to="/login" class="link-primary">立即登录</router-link>
        </div>
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

const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
})

async function handleSubmit() {
  // Basic validation
  if (!form.username || !form.email || !form.password || !form.confirmPassword) {
    ElMessage.warning('请填写所有字段')
    return
  }

  if (form.username.length < 3 || form.username.length > 50) {
    ElMessage.warning('用户名长度应为 3-50 个字符')
    return
  }

  if (form.password.length < 8) {
    ElMessage.warning('密码至少8个字符')
    return
  }

  if (form.password !== form.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }

  loading.value = true
  try {
    await authStore.register(form.username, form.email, form.password)
    ElMessage.success('注册成功')
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
  background: #F2F9F4;
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

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
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

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.auth-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: #6B7D72;
}

.link-primary {
  color: #5A9672;
  font-weight: 600;
}

.link-primary:hover { color: #4A7D5F; }
</style>
