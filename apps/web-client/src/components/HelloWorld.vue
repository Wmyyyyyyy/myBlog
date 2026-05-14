<template>
  <div class="hello-world">
    <h1>{{ msg }}</h1>
    <p>
      For a guide and recipes on how to configure / customize this project,<br />
      check out the
      <a href="https://vitejs.dev/guide/" target="_blank" rel="noopener">Vite documentation</a>.
    </p>
    <h3>Installed IDE Plugins</h3>
    <ul>
      <li><a href="https://github.com/vuejs/vue-tsc" target="_blank" rel="noopener">vue-tsc</a></li>
    </ul>
    <h3>Essential Links</h3>
    <ul>
      <li><a href="https://vitejs.dev/guide/" target="_blank" rel="noopener">Vite Docs</a></li>
      <li><a href="https://vuejs.org/" target="_blank" rel="noopener">Vue Docs</a></li>
    </ul>
  </div>
</template>

<script setup>
defineProps({
  msg: {
    type: String,
    default: 'Hello Vue 3 + Vite!',
  },
})
</script>

<style scoped>
.hello-world {
  padding: 20px;
}

h1 {
  color: #42b983;
}

h3 {
  margin: 16px 0 8px;
}

ul {
  list-style-type: disc;
  padding-left: 20px;
}

li {
  margin: 4px 0;
}

a {
  color: #42b983;
}
</style>
