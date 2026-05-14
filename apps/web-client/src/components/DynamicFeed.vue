<template>
  <div class="dynamic-feed">
    <h3>动态</h3>
    <div class="feed-list">
      <DynamicItem v-for="event in store.events" :key="event.id" :event="event" />
    </div>
    <div v-if="store.nextCursor" class="load-more">
      <button @click="loadMore" :disabled="store.isLoading">
        {{ store.isLoading ? '加载中...' : '加载更多' }}
      </button>
    </div>
    <div v-else-if="!store.isLoading && store.events.length === 0" class="empty">
      暂无动态
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useDynamicsStore } from '@/stores/dynamics'
import DynamicItem from './DynamicItem.vue'

const store = useDynamicsStore()

onMounted(() => {
  store.fetchFeed()
})

function loadMore() {
  store.fetchFeed()
}
</script>

<style scoped>
.dynamic-feed { padding: 16px; }
.feed-list { margin-top: 16px; }
.load-more { text-align: center; margin-top: 16px; }
.load-more button { padding: 8px 24px; background: #5a9672; color: white; border: none; border-radius: 8px; cursor: pointer; }
.load-more button:disabled { opacity: 0.5; }
.empty { text-align: center; color: #6b7d72; padding: 32px; }
</style>
