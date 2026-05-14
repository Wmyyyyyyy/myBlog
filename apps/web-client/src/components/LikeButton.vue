<template>
  <button @click="handleClick" class="like-btn" :class="{ liked: isLiked }">
    <span class="icon">{{ isLiked ? '❤️' : '🤍' }}</span>
    <span class="count">{{ likeCount }}</span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useInteractionStore } from '@/stores/interactions'

const props = defineProps({
  blogId: { type: String, required: true },
  initialLiked: { type: Boolean, default: false },
  initialCount: { type: Number, default: 0 }
})

const interactionStore = useInteractionStore()

const isLiked = computed(() => interactionStore.likeStatus[props.blogId]?.is_liked ?? props.initialLiked)
const likeCount = computed(() => interactionStore.likeStatus[props.blogId]?.like_count ?? props.initialCount)

async function handleClick() {
  await interactionStore.toggleLike(props.blogId)
}
</script>

<style scoped>
.like-btn { display: flex; align-items: center; gap: 4px; background: none; border: none; cursor: pointer; }
.like-btn.liked { color: #e24; }
</style>
