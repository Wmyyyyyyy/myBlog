<template>
  <div class="foundation-page">
    <div class="header">
      <h1>百日筑基</h1>
      <p class="subtitle">每天进步一点点</p>
    </div>

    <div class="checkin-card">
      <div class="streak-info">
        <div class="streak-item">
          <span class="number">{{ store.status.current_streak }}</span>
          <span class="label">当前连续</span>
        </div>
        <div class="streak-item">
          <span class="number">{{ store.status.longest_streak }}</span>
          <span class="label">历史最长</span>
        </div>
      </div>

      <div class="checkin-status">
        {{ store.status.message }}
      </div>

      <button
        class="checkin-btn"
        :class="{ checked: store.status.today_checked_in }"
        :disabled="store.status.today_checked_in"
        @click="handleCheckin"
      >
        {{ store.status.today_checked_in ? '已打卡' : '立即打卡' }}
      </button>
    </div>

    <div class="history-section">
      <h3>打卡记录</h3>
      <div class="history-list">
        <div v-for="record in store.history" :key="record.check_in_date" class="history-item">
          <span class="date">{{ formatDate(record.check_in_date) }}</span>
          <span class="check-icon">✓</span>
        </div>
        <div v-if="store.history.length === 0" class="empty">
          暂无打卡记录
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useFoundationStore } from '@/stores/foundation'

const store = useFoundationStore()

onMounted(() => {
  store.fetchStatus()
  store.fetchHistory()
})

async function handleCheckin() {
  await store.checkIn()
}

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<style scoped>
.foundation-page {
  max-width: 600px;
  margin: 0 auto;
  padding: 24px;
}

.header {
  text-align: center;
  margin-bottom: 32px;
}

.header h1 {
  color: #2d3b30;
  font-size: 28px;
}

.subtitle {
  color: #6b7d72;
  margin-top: 8px;
}

.checkin-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  text-align: center;
}

.streak-info {
  display: flex;
  justify-content: center;
  gap: 48px;
  margin-bottom: 24px;
}

.streak-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.streak-item .number {
  font-size: 48px;
  font-weight: 700;
  color: #5a9672;
}

.streak-item .label {
  font-size: 14px;
  color: #6b7d72;
  margin-top: 4px;
}

.checkin-status {
  color: #2d3b30;
  font-size: 16px;
  margin-bottom: 24px;
}

.checkin-btn {
  width: 100%;
  padding: 16px;
  font-size: 18px;
  font-weight: 600;
  color: white;
  background: #5a9672;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.2s;
}

.checkin-btn:hover:not(:disabled) {
  background: #4a8562;
}

.checkin-btn:disabled {
  background: #97c9a8;
  cursor: default;
}

.checkin-btn.checked {
  background: #97c9a8;
}

.history-section {
  margin-top: 32px;
}

.history-section h3 {
  color: #2d3b30;
  margin-bottom: 16px;
}

.history-list {
  background: #ffffff;
  border-radius: 16px;
  padding: 16px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #ddeee5;
}

.history-item:last-child {
  border-bottom: none;
}

.history-item .date {
  color: #2d3b30;
}

.history-item .check-icon {
  color: #5a9672;
  font-weight: bold;
}

.empty {
  text-align: center;
  color: #6b7d72;
  padding: 24px;
}
</style>
