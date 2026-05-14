<template>
  <div id="app">
    <TheNavbar />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import TheNavbar from '@/components/TheNavbar.vue'
</script>

<style scoped>
#app {
  min-height: 100vh;
}

.main-content {
  padding-top: 60px;
}
</style>
