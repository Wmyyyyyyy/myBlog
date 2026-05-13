<template>
  <el-avatar :size="size" :src="user?.avatar" :style="avatarStyle">
    <el-icon><User /></el-icon>
  </el-avatar>
</template>

<script setup>
defineProps({
  user: {
    type: Object,
    default: null,
  },
  size: {
    type: [Number, String],
    default: 40,
  },
})

const avatarStyle = {
  background: 'linear-gradient(135deg, #97C9A8 0%, #5A9672 100%)',
  color: '#FFFFFF',
  border: '2px solid #DDEEE5',
}
</script>
