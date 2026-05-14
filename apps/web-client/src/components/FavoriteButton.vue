<template>
  <button @click="handleClick" class="fav-btn" :class="{ favorited: isFavorited }">
    <span class="icon">{{ isFavorited ? '⭐' : '☆' }}</span>
    <span class="count">{{ favCount }}</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useInteractionStore } from '@/stores/interactions'

const props = defineProps({
  blogId: { type: String, required: true },
  initialFavorited: { type: Boolean, default: false },
  initialCount: { type: Number, default: 0 }
})

const interactionStore = useInteractionStore()

const isFavorited = computed(() => interactionStore.favoriteStatus[props.blogId]?.is_favorited ?? props.initialFavorited)
const favCount = computed(() => interactionStore.favoriteStatus[props.blogId]?.favorite_count ?? props.initialCount)

async function handleClick() {
  await interactionStore.toggleFavorite(props.blogId)
}
</script>

<style scoped>
.fav-btn { display: flex; align-items: center; gap: 4px; background: none; border: none; cursor: pointer; }
.fav-btn.favorited { color: #f80; }
</style>
