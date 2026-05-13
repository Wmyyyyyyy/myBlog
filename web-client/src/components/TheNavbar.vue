<template>
  <nav class="navbar">
    <div class="navbar-inner">
      <router-link to="/blogs" class="navbar-brand">
        <div class="navbar-brand-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z"/>
            <path d="M2 17l10 5 10-5"/>
            <path d="M2 12l10 5 10-5"/>
          </svg>
        </div>
        <span class="navbar-brand-text">静心启慧</span>
      </router-link>

      <div class="navbar-links">
        <router-link to="/blogs" class="navbar-link" :class="{ active: $route.path === '/blogs' }">
          首页
        </router-link>
        <router-link to="/profile" class="navbar-link">
          个人中心
        </router-link>
        <div class="navbar-divider"></div>
        <div class="navbar-avatar" @click="$router.push('/profile')">
          <UserAvatar :user="user" :size="34" />
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import UserAvatar from './UserAvatar.vue'

const authStore = useAuthStore()
const user = authStore.user
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid #DDEEE5;
  box-shadow: 0 1px 3px rgba(45,59,48,0.06);
}

.navbar-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 24px;
  height: 64px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.navbar-brand-icon {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #5A9672 0%, #97C9A8 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.navbar-brand-icon svg { width: 18px; height: 18px; color: white; }

.navbar-brand-text {
  font-family: 'Lora', 'Noto Serif SC', Georgia, serif;
  font-size: 17px;
  font-weight: 700;
  color: #2D3B30;
}

.navbar-links {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: auto;
}

.navbar-link {
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #6B7D72;
  transition: all 150ms ease;
  cursor: pointer;
}

.navbar-link:hover {
  color: #2D3B30;
  background: #E8F0EB;
}

.navbar-link.active {
  color: #5A9672;
  background: #E8F5ED;
}

.navbar-divider {
  width: 1px;
  height: 20px;
  background: #C8DCD2;
  margin: 0 8px;
}

.navbar-avatar {
  cursor: pointer;
  border-radius: 50%;
  transition: transform 150ms ease;
}

.navbar-avatar:hover {
  transform: scale(1.05);
}
</style>
