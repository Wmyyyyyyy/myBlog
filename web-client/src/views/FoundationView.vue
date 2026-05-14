<template>
  <div class="foundation-page">
    <div class="foundation-hero">
      <div class="hero-content">
        <h1>百日筑基</h1>
        <p>每天静心，养成好习惯</p>
      </div>
      <div class="hero-decoration">
        <div class="deco-circle"></div>
        <div class="deco-circle"></div>
        <div class="deco-circle"></div>
      </div>
    </div>

    <div class="foundation-content">
      <!-- Status Card with Progress Ring -->
      <div class="status-card">
        <div class="status-left">
          <div class="streak-ring">
            <svg viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="45" fill="none" stroke="#E8F5ED" stroke-width="8"/>
              <circle cx="50" cy="50" r="45" fill="none" stroke="#5A9672" stroke-width="8"
                stroke-dasharray="283"
                :stroke-dashoffset="283 - (283 * Math.min(foundationStore.todayStatus.streak / 100, 1))"
                stroke-linecap="round"
                transform="rotate(-90 50 50)"/>
            </svg>
            <div class="ring-content">
              <span class="streak-number">{{ foundationStore.todayStatus.streak }}</span>
              <span class="streak-label">天</span>
            </div>
          </div>
        </div>
        <div class="status-right">
          <div class="status-info">
            <div class="info-item">
              <span class="info-value">{{ foundationStore.history.total_checkins }}</span>
              <span class="info-label">总打卡</span>
            </div>
            <div class="info-item">
              <span class="info-value">{{ foundationStore.history.longest_streak }}</span>
              <span class="info-label">最长连续</span>
            </div>
          </div>
          <button
            class="checkin-btn"
            :class="{ checked: foundationStore.todayStatus.checked_in }"
            :disabled="foundationStore.todayStatus.checked_in"
            @click="handleCheckIn"
          >
            {{ foundationStore.todayStatus.checked_in ? '✓ 今日已打卡' : '立即打卡' }}
          </button>
        </div>
      </div>

      <!-- Achievements Section -->
      <div class="achievements-section">
        <div class="section-header">
          <h3>成就徽章</h3>
          <span class="achievement-count">{{ unlockedCount }}/{{ foundationStore.achievements.length }}</span>
        </div>
        <div class="achievements-scroll">
          <div
            v-for="achievement in foundationStore.achievements"
            :key="achievement.type"
            class="achievement-badge"
            :class="{ unlocked: achievement.unlocked }"
          >
            <div class="badge-icon">
              <svg v-if="achievement.unlocked" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
              </svg>
              <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2"/>
                <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
            </div>
            <span class="badge-name">{{ achievement.name }}</span>
          </div>
        </div>
      </div>

      <!-- Calendar Section -->
      <div class="calendar-section">
        <div class="section-header">
          <h3>{{ currentMonth }}</h3>
        </div>
        <div class="calendar-wrapper">
          <div class="calendar-header">
            <span v-for="day in ['日', '一', '二', '三', '四', '五', '六']" :key="day">{{ day }}</span>
          </div>
          <div class="calendar-grid">
            <div
              v-for="(day, index) in calendarDays"
              :key="index"
              class="calendar-cell"
              :class="{
                checked: day.checked,
                today: day.isToday,
                future: day.isFuture,
                empty: !day.date
              }"
            >
              <span v-if="day.date" class="day-number">{{ day.day }}</span>
              <div v-if="day.checked" class="check-dot"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useFoundationStore } from '@/stores/foundation'

const foundationStore = useFoundationStore()

onMounted(() => {
  foundationStore.fetchAll()
})

const currentMonth = computed(() => {
  const now = new Date()
  return now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' })
})

const unlockedCount = computed(() =>
  foundationStore.achievements.filter(a => a.unlocked).length
)

const calendarDays = computed(() => {
  const result = []
  const today = new Date()
  const year = today.getFullYear()
  const month = today.getMonth()
  const todayStr = `${year}-${month + 1}-${today.getDate()}`

  const firstDay = new Date(year, month, 1).getDay()
  const daysInMonth = new Date(year, month + 1, 0).getDate()

  const checkedDates = new Set(
    foundationStore.history.dates?.map(d => {
      const date = new Date(d)
      return `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`
    }) || []
  )

  for (let i = 0; i < firstDay; i++) {
    result.push({ date: '', day: null, checked: false, isToday: false, isFuture: false })
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = `${year}-${month + 1}-${d}`
    result.push({
      date: dateStr,
      day: d,
      checked: checkedDates.has(dateStr),
      isToday: dateStr === todayStr,
      isFuture: new Date(year, month, d) > today,
    })
  }

  return result
})

async function handleCheckIn() {
  try {
    const result = await foundationStore.checkIn()
    ElMessage.success('打卡成功！')
    if (result.achieved_achievements.length > 0) {
      ElMessage.info(`解锁成就: ${result.achieved_achievements.join(', ')}`)
    }
  } catch (error) {
    // Error handled by interceptor
  }
}
</script>

<style scoped>
.foundation-page { min-height: 100vh; background: #F2F9F4; padding-bottom: 40px; }

.foundation-hero {
  background: linear-gradient(180deg, rgba(232,245,237,0.8) 0%, #F2F9F4 100%);
  padding: 48px 24px 32px;
  text-align: center;
  position: relative;
  overflow: hidden;
}
.hero-content h1 {
  font-family: 'Lora', 'Noto Serif SC', Georgia, serif;
  font-size: 28px;
  font-weight: 700;
  color: #2D3B30;
  margin-bottom: 8px;
}
.hero-content p { font-size: 15px; color: #6B7D72; }
.hero-decoration {
  position: absolute;
  top: -30px;
  right: -30px;
  display: flex;
  gap: 8px;
}
.deco-circle {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(90,150,114,0.1), rgba(151,201,168,0.2));
}

.foundation-content { max-width: 600px; margin: 0 auto; padding: 0 16px; display: flex; flex-direction: column; gap: 16px; }

.status-card {
  background: #FFFFFF;
  border-radius: 20px;
  padding: 24px;
  display: flex;
  gap: 24px;
  align-items: center;
  border: 1px solid #DDEEE5;
  box-shadow: 0 4px 12px rgba(45,59,48,0.06);
}
.streak-ring {
  width: 100px;
  height: 100px;
  position: relative;
}
.streak-ring svg { width: 100%; height: 100%; }
.ring-content {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.streak-number { font-size: 32px; font-weight: 700; color: #5A9672; line-height: 1; }
.streak-label { font-size: 12px; color: #6B7D72; }
.status-right { flex: 1; }
.status-info { display: flex; gap: 20px; margin-bottom: 16px; }
.info-item { display: flex; flex-direction: column; }
.info-value { font-size: 20px; font-weight: 700; color: #2D3B30; }
.info-label { font-size: 12px; color: #6B7D72; }
.checkin-btn {
  width: 100%;
  padding: 12px 20px;
  border-radius: 12px;
  border: none;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  background: linear-gradient(135deg, #5A9672 0%, #7BAF8E 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 12px rgba(90,150,114,0.3);
  transition: all 150ms ease;
}
.checkin-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(90,150,114,0.4); }
.checkin-btn.checked { background: #E8F5ED; color: #5A9672; box-shadow: none; cursor: default; }

.achievements-section {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #DDEEE5;
}
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-header h3 { font-size: 16px; font-weight: 600; color: #2D3B30; }
.achievement-count { font-size: 13px; color: #6B7D72; }
.achievements-scroll { display: flex; gap: 12px; overflow-x: auto; padding-bottom: 8px; }
.achievements-scroll::-webkit-scrollbar { display: none; }
.achievement-badge {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  background: #F9FAFA;
  border-radius: 12px;
  min-width: 72px;
  border: 1px solid transparent;
}
.achievement-badge.unlocked { background: #E8F5ED; border-color: #97C9A8; }
.badge-icon { width: 28px; height: 28px; color: #C8DCD2; }
.achievement-badge.unlocked .badge-icon { color: #5A9672; }
.badge-name { font-size: 12px; color: #6B7D72; white-space: nowrap; }
.achievement-badge.unlocked .badge-name { color: #2D3B30; font-weight: 500; }

.calendar-section {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid #DDEEE5;
}
.calendar-wrapper {}
.calendar-header {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-size: 12px;
  color: #6B7D72;
  margin-bottom: 8px;
}
.calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
.calendar-cell {
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 13px;
  color: #2D3B30;
  position: relative;
  background: #F9FAFA;
}
.calendar-cell.checked { background: #5A9672; color: #FFFFFF; }
.calendar-cell.today { border: 2px solid #5A9672; }
.calendar-cell.future { opacity: 0.4; }
.calendar-cell.empty { background: transparent; }
.day-number { font-weight: 500; }
.check-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255,255,255,0.8);
  position: absolute;
  bottom: 4px;
}
</style>
