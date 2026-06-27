<template>
  <div class="rink-view">
    <h1>Pittsburgh Penguins xG Analyzer</h1>
    <p class="instructions">
      Click anywhere on the rink to calculate Expected Goals (xG) for that shot location. Adjust
      shot parameters using the controls above the rink.
    </p>
    <RinkVisualization />
  </div>
</template>

<script setup lang="ts">
import RinkVisualization from '@/components/RinkVisualization.vue'
</script>

<style scoped>
.rink-view {
  padding: 20px;
}

h1 {
  text-align: center;
  color: #fcb514;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  margin-bottom: 10px;
}

.instructions {
  text-align: center;
  color: #666;
  margin-bottom: 30px;
  font-size: 1.1em;
}
</style>
