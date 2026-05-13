<template>
  <nav class="navbar">
    <div class="navbar-container">
      <router-link to="/blogs" class="logo">
        <el-icon><document /></el-icon>
        <span>我的博客</span>
      </router-link>
      <div class="nav-links">
        <template v-if="isLoggedIn">
          <span class="username">{{ user?.username }}</span>
          <el-button type="danger" size="small" @click="handleLogout">退出</el-button>
        </template>
        <template v-else>
          <router-link to="/login">
            <el-button type="primary" size="small">登录</el-button>
          </router-link>
          <router-link to="/register">
            <el-button size="small">注册</el-button>
          </router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { ElMessage } from 'element-plus'

const router = useRouter()
const { isLoggedIn, user, logout } = useAuth()

function handleLogout() {
  logout()
  ElMessage.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.navbar-container {
  max-width: 1200px;
  height: 100%;
  margin: 0 auto;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
}

.logo .el-icon {
  font-size: 24px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  color: #666;
  margin-right: 8px;
}
</style>
