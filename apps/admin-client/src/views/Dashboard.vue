<template>
  <div class="dashboard">
    <h2>数据概览</h2>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: #E8F5ED;">
          <el-icon size="24" color="#5A9672"><User /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.total_users }}</span>
          <span class="stat-label">总用户数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #FFF3E0;">
          <el-icon size="24" color="#FF9800;"><Document /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.total_blogs }}</span>
          <span class="stat-label">总博客数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #E3F2FD;">
          <el-icon size="24" color="#2196F3;"><ChatDotRound /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.total_comments }}</span>
          <span class="stat-label">总评论数</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: #FCE4EC;">
          <el-icon size="24" color="#E91E63;"><Star /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ stats.total_likes }}</span>
          <span class="stat-label">总点赞数</span>
        </div>
      </div>
    </div>

    <!-- 今日新增 -->
    <div class="today-stats">
      <h3>今日新增</h3>
      <div class="today-grid">
        <div class="today-item">
          <span class="today-value">{{ stats.today_new_users }}</span>
          <span class="today-label">新用户</span>
        </div>
        <div class="today-item">
          <span class="today-value">{{ stats.today_new_blogs }}</span>
          <span class="today-label">新博客</span>
        </div>
        <div class="today-item">
          <span class="today-value">{{ stats.today_new_comments }}</span>
          <span class="today-label">新评论</span>
        </div>
      </div>
    </div>

    <!-- 图表 -->
    <div class="charts-grid">
      <div class="chart-card">
        <h3>用户增长</h3>
        <div ref="userChartRef" class="chart"></div>
      </div>
      <div class="chart-card">
        <h3>博客增长</h3>
        <div ref="blogChartRef" class="chart"></div>
      </div>
      <div class="chart-card">
        <h3>互动统计</h3>
        <div ref="interactionChartRef" class="chart"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import * as echarts from 'echarts'
import client from '@/api'

const stats = reactive({
  total_users: 0, total_blogs: 0, total_comments: 0, total_likes: 0,
  today_new_users: 0, today_new_blogs: 0, today_new_comments: 0,
})

const userChartRef = ref(null)
const blogChartRef = ref(null)
const interactionChartRef = ref(null)

onMounted(async () => {
  await loadStats()
  await loadCharts()
})

async function loadStats() {
  try {
    const response = await client.get('/dashboard/stats')
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('Failed to load stats', error)
  }
}

async function loadCharts() {
  try {
    const [userRes, blogRes, interactionRes] = await Promise.all([
      client.get('/dashboard/user-growth'),
      client.get('/dashboard/blog-growth'),
      client.get('/dashboard/interactions'),
    ])

    // 用户增长图
    const userChart = echarts.init(userChartRef.value)
    userChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: userRes.data.map(d => d.date) },
      yAxis: { type: 'value' },
      series: [{ data: userRes.data.map(d => d.count), type: 'line', smooth: true, areaStyle: { color: '#E8F5ED' }, lineStyle: { color: '#5A9672' }, itemStyle: { color: '#5A9672' } }],
    })

    // 博客增长图
    const blogChart = echarts.init(blogChartRef.value)
    blogChart.setOption({
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: blogRes.data.map(d => d.date) },
      yAxis: { type: 'value' },
      series: [{ data: blogRes.data.map(d => d.count), type: 'bar', itemStyle: { color: '#5A9672' } }],
    })

    // 互动统计图
    const interactionChart = echarts.init(interactionChartRef.value)
    interactionChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['点赞', '评论', '关注'] },
      xAxis: { type: 'category', data: interactionRes.data.map(d => d.date) },
      yAxis: { type: 'value' },
      series: [
        { name: '点赞', data: interactionRes.data.map(d => d.likes), type: 'line', itemStyle: { color: '#E91E63' } },
        { name: '评论', data: interactionRes.data.map(d => d.comments), type: 'line', itemStyle: { color: '#2196F3' } },
        { name: '关注', data: interactionRes.data.map(d => d.follows), type: 'line', itemStyle: { color: '#FF9800' } },
      ],
    })
  } catch (error) {
    console.error('Failed to load charts', error)
  }
}
</script>

<style scoped>
.dashboard { max-width: 1200px; }
.dashboard h2 { font-size: 24px; margin-bottom: 24px; }
.dashboard h3 { font-size: 16px; margin-bottom: 16px; color: #2D3B30; }

.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card {
  background: #FFFFFF; border-radius: 12px; padding: 20px;
  display: flex; align-items: center; gap: 16px;
  border: 1px solid #DDEEE5;
}
.stat-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; }
.stat-value { font-size: 28px; font-weight: 700; color: #2D3B30; display: block; }
.stat-label { font-size: 13px; color: #6B7D72; }

.today-stats { background: #FFFFFF; border-radius: 12px; padding: 20px; margin-bottom: 24px; border: 1px solid #DDEEE5; }
.today-grid { display: flex; gap: 48px; }
.today-item { display: flex; flex-direction: column; }
.today-value { font-size: 24px; font-weight: 700; color: #5A9672; }
.today-label { font-size: 13px; color: #6B7D72; }

.charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
.chart-card { background: #FFFFFF; border-radius: 12px; padding: 20px; border: 1px solid #DDEEE5; }
.chart-card:last-child { grid-column: span 2; }
.chart { height: 250px; }
</style>
