<template>
  <button @click="handleClick" class="follow-btn" :class="{ following: isFollowing }">
    {{ isFollowing ? '已关注' : '关注' }}
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useInteractionStore } from '@/stores/interactions'

const props = defineProps({
  userId: { type: String, required: true },
  initialFollowing: { type: Boolean, default: false }
})

const interactionStore = useInteractionStore()

const isFollowing = computed(() => interactionStore.followStatus[props.userId]?.is_following ?? props.initialFollowing)

async function handleClick() {
  await interactionStore.toggleFollow(props.userId)
}
</script>

<style scoped>
.follow-btn {
  padding: 6px 16px;
  border: 1px solid #5a9672;
  border-radius: 6px;
  background: transparent;
  color: #5a9672;
  cursor: pointer;
  font-size: 14px;
}
.follow-btn.following {
  background: #5a9672;
  color: white;
}
</style>
