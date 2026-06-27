<template>
  <div class="analytics-view">
    <h1>Hockey Analytics Dashboard</h1>
    <p class="coming-soon">Advanced analytics coming soon...</p>

    <div class="placeholder-cards">
      <div class="card">
        <h3>Player Impact Scores</h3>
        <p>Track individual player contributions to Expected Goals</p>
      </div>

      <div class="card">
        <h3>Line Chemistry Analysis</h3>
        <p>Optimize line combinations based on performance metrics</p>
      </div>

      <div class="card">
        <h3>Game Momentum Tracker</h3>
        <p>Real-time momentum shifts and predictive analytics</p>
      </div>

      <div class="card">
        <h3>Shot Pattern Analysis</h3>
        <p>Heat maps and tendency reports for opponents</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Future analytics components will go here
</script>

<style scoped>
.analytics-view {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

h1 {
  text-align: center;
  color: #333;
  margin-bottom: 20px;
}

.coming-soon {
  text-align: center;
  color: #666;
  font-size: 1.2em;
  margin-bottom: 40px;
}

.placeholder-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 40px;
}

.card {
  background: #f5f5f5;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.card h3 {
  color: #fcb514;
  margin-bottom: 15px;
}

.card p {
  color: #666;
  line-height: 1.6;
}
</style>
