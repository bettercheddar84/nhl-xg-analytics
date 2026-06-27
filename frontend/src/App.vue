<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
</script>

<template>
  <header>
    <div class="wrapper">
      <nav>
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/rink">xG Visualizer</RouterLink>
        <RouterLink to="/analytics">Analytics</RouterLink>
      </nav>
    </div>
  </header>

  <RouterView />
</template>

<style scoped>
header {
  background-color: #000;
  padding: 1rem 0;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.wrapper {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

nav {
  display: flex;
  gap: 2rem;
  justify-content: center;
}

nav a {
  color: #fcb514;
  text-decoration: none;
  font-weight: 500;
  font-size: 1.1rem;
  transition: color 0.3s;
}

nav a:hover {
  color: #fff;
}

nav a.router-link-exact-active {
  color: #fff;
  border-bottom: 2px solid #fcb514;
}
</style>
