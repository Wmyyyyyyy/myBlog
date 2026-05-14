<template>
  <div class="admin-layout">
    <aside class="sidebar">
      <div class="logo">
        <h1>Admin</h1>
      </div>
      <nav class="nav">
        <router-link to="/dashboard" class="nav-item">
          <el-icon><DataAnalysis /></el-icon>
          <span>Dashboard</span>
        </router-link>
        <router-link to="/users" class="nav-item">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </router-link>
        <router-link to="/sensitive-words" class="nav-item">
          <el-icon><Warning /></el-icon>
          <span>敏感词</span>
        </router-link>
        <router-link to="/review" class="nav-item">
          <el-icon><DocumentChecked /></el-icon>
          <span>内容审核</span>
        </router-link>
        <router-link to="/logs" class="nav-item">
          <el-icon><Operation /></el-icon>
          <span>操作日志</span>
        </router-link>
        <router-link to="/security" class="nav-item">
          <el-icon><Shield /></el-icon>
          <span>安全中心</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <router-link to="/" class="nav-item" target="_blank">
          <el-icon><View /></el-icon>
          <span>返回主站</span>
        </router-link>
        <button class="nav-item" @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>
          <span>退出登录</span>
        </button>
      </div>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function handleLogout() {
  localStorage.removeItem('admin_token')
  router.push('/login')
}
</script>

<style scoped>
.admin-layout { display: flex; min-height: 100vh; }

.sidebar {
  width: 220px;
  background: #2D3B30;
  color: #FFFFFF;
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
}

.logo { padding: 24px 16px; border-bottom: 1px solid rgba(255,255,255,0.1); }
.logo h1 { font-size: 20px; font-weight: 600; color: #5A9672; }

.nav { flex: 1; padding: 16px 0; }
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255,255,255,0.7);
  text-decoration: none;
  font-size: 14px;
  transition: all 200ms;
  border: none;
  background: none;
  width: 100%;
  cursor: pointer;
}
.nav-item:hover { background: rgba(255,255,255,0.1); color: #FFFFFF; }
.nav-item.router-link-active { background: rgba(90,150,114,0.3); color: #5A9672; }

.sidebar-footer { padding: 16px 0; border-top: 1px solid rgba(255,255,255,0.1); }

.main-content { flex: 1; margin-left: 220px; padding: 24px; background: #F2F9F4; min-height: 100vh; }
</style>
