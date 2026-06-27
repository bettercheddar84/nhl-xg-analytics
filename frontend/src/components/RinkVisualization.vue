<template>
  <div class="rink-container">
    <h2>Expected Goals (xG) Visualizer</h2>

    <!-- Mode selector -->
    <div class="mode-selector">
      <label> <input type="radio" v-model="mode" value="interactive" /> Interactive Mode </label>
      <label> <input type="radio" v-model="mode" value="nhl-data" /> NHL Game Data </label>
    </div>

    <!-- Interactive controls -->
    <div v-if="mode === 'interactive'" class="controls">
      <label>
        Shot Type:
        <select v-model="shotType">
          <option>Wrist</option>
          <option>Slap</option>
          <option>Snap</option>
          <option>Backhand</option>
          <option>Tip-In</option>
          <option>Deflection</option>
        </select>
      </label>
      <label> <input type="checkbox" v-model="isRebound" /> Rebound </label>
      <label> <input type="checkbox" v-model="isRush" /> Rush </label>
      <button @click="clearShots" class="clear-btn">Clear Shots</button>
    </div>

    <div class="shooting-direction">
      <span> Shoot this direction at right goal →</span>
    </div>

    <!-- NHL Data controls -->
    <div v-if="mode === 'nhl-data'" class="nhl-controls">
      <label>
        Game:
        <select v-model="selectedGame">
          <option value="">Select a game...</option>
          <option value="2024-01-15">vs. Seattle - Jan 15, 2024</option>
          <option value="2024-01-20">@ Tampa Bay - Jan 20, 2024</option>
        </select>
      </label>
      <label>
        Period:
        <select v-model="selectedPeriod">
          <option value="all">All Periods</option>
          <option value="1">1st Period</option>
          <option value="2">2nd Period</option>
          <option value="3">3rd Period</option>
        </select>
      </label>
      <label>
        Player:
        <select v-model="selectedPlayer">
          <option value="">All Players</option>
          <option value="crosby">Sidney Crosby</option>
          <option value="malkin">Evgeni Malkin</option>
          <option value="letang">Kris Letang</option>
          <option value="rust">Bryan Rust</option>
        </select>
      </label>
    </div>

    <!-- NHL Rink Component -->
    <NHLRink
      :width="800"
      :height="340"
      :shots="displayShots"
      :current-shot="currentShot"
      :selected-shot="selectedShot"
      @rink-click="handleRinkClick"
      @shot-click="handleShotClick"
    />

    <!-- Shot Analysis Panel -->
    <div v-if="lastPrediction || selectedShot" class="prediction-result">
      <h3>Shot Analysis</h3>
      <div class="metrics">
        <div class="metric">
          <span class="label">Expected Goals:</span>
          <span class="value" :class="getShotQualityClass(currentXG)">
            {{ (currentXG * 100).toFixed(1) }}%
          </span>
        </div>
        <div class="metric">
          <span class="label">Shot Quality:</span>
          <span class="value" :class="getShotQualityClass(currentXG)">
            {{ getShotQuality(currentXG) }}
          </span>
        </div>
        <div class="metric">
          <span class="label">Distance:</span>
          <span class="value">{{ currentDistance.toFixed(1) }} ft</span>
        </div>
        <div class="metric">
          <span class="label">Angle:</span>
          <span class="value">{{ Math.abs(currentAngle).toFixed(1) }}°</span>
        </div>
      </div>

      <div v-if="selectedShot && selectedShot.player" class="shot-details">
        <div class="detail">
          <span class="label">Player:</span>
          <span class="value">{{ selectedShot.player }}</span>
        </div>
        <div class="detail">
          <span class="label">Time:</span>
          <span class="value">{{ selectedShot.time }} (P{{ selectedShot.period }})</span>
        </div>
        <div class="detail">
          <span class="label">Shot Type:</span>
          <span class="value">{{ selectedShot.type }}</span>
        </div>
      </div>

      <div class="shot-modifiers">
        <span v-if="isRebound" class="modifier rebound">REBOUND</span>
        <span v-if="isRush" class="modifier rush">RUSH</span>
        <span class="modifier">{{ currentShotType }}</span>
      </div>

      <p class="recommendation">{{ getRecommendation(currentXG) }}</p>
    </div>

    <div v-if="loading" class="loading">Calculating xG...</div>
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { calculateShotMetrics, svgToNhl } from '@/types/rinkDimensions'
import axios from 'axios'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import NHLRink from './NHLRink.vue'

// Around line 130, after refs
const ws = ref<WebSocket | null>(null)

// In onMounted() lifecycle hook
onMounted(() => {
  if (mode.value === 'nhl-data' && selectedGame.value) {
    ws.value = new WebSocket(`ws://localhost:8000/ws/game/${selectedGame.value}`)
    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.event === 'shot') {
        nhlShots.value.push({
          x: data.location.x,
          y: data.location.y,
          xg: data.xG,
          player: data.player,
          time: data.time,
        })
      }
    }
  }
})

// Clean up on unmount
onBeforeUnmount(() => {
  ws.value?.close()
})

// Mode selection
const mode = ref<'interactive' | 'nhl-data'>('interactive')

// Interactive mode data
const shotType = ref('Wrist')
const isRebound = ref(false)
const isRush = ref(false)
const interactiveShots = ref<any[]>([])
const currentShot = ref<any>(null)

// NHL data mode
const selectedGame = ref('')
const selectedPeriod = ref('all')
const selectedPlayer = ref('')
const nhlShots = ref<any[]>([])
const selectedShot = ref<any>(null)

// Common data
const lastPrediction = ref<any>(null)
const loading = ref(false)
const error = ref('')

// Computed properties
const displayShots = computed(() => {
  if (mode.value === 'interactive') {
    return interactiveShots.value
  } else {
    let shots = nhlShots.value
    if (selectedPeriod.value !== 'all') {
      shots = shots.filter((s) => s.period === parseInt(selectedPeriod.value))
    }
    if (selectedPlayer.value) {
      shots = shots.filter((s) => s.player?.toLowerCase().includes(selectedPlayer.value))
    }
    return shots
  }
})

const currentXG = computed(() => {
  if (selectedShot.value?.xg) return selectedShot.value.xg
  if (lastPrediction.value?.expected_goals) return lastPrediction.value.expected_goals
  return 0
})

const currentDistance = computed(() => {
  if (selectedShot.value?.distance) return selectedShot.value.distance
  if (currentShot.value) {
    const nhlCoords = svgToNhl(currentShot.value.x, currentShot.value.y, 200, 85)
    return calculateShotMetrics(nhlCoords.x, nhlCoords.y).distance
  }
  return 0
})

const currentAngle = computed(() => {
  if (selectedShot.value?.angle) return selectedShot.value.angle
  if (currentShot.value) {
    const nhlCoords = svgToNhl(currentShot.value.x, currentShot.value.y, 200, 85)
    return calculateShotMetrics(nhlCoords.x, nhlCoords.y).angle
  }
  return 0
})

const currentShotType = computed(() => {
  return selectedShot.value?.type || shotType.value
})

// Watch for parameter changes
watch([shotType, isRebound, isRush], () => {
  if (mode.value === 'interactive' && currentShot.value) {
    predictXG()
  }
})

// Load NHL game data when game is selected
watch(selectedGame, async (gameId) => {
  if (gameId) {
    // Load sample NHL shot data
    nhlShots.value = [
      {
        x: 150,
        y: 35,
        xg: 0.12,
        player: 'Sidney Crosby',
        period: 1,
        time: '5:23',
        type: 'Wrist',
        distance: 25,
        angle: 15,
      },
      {
        x: 170,
        y: 42.5,
        xg: 0.35,
        player: 'Jake Guentzel',
        period: 1,
        time: '8:45',
        type: 'Tip-In',
        distance: 12,
        angle: 0,
      },
      {
        x: 140,
        y: 25,
        xg: 0.08,
        player: 'Evgeni Malkin',
        period: 2,
        time: '12:10',
        type: 'Slap',
        distance: 40,
        angle: 30,
      },
      {
        x: 165,
        y: 50,
        xg: 0.22,
        player: 'Bryan Rust',
        period: 2,
        time: '15:30',
        type: 'Snap',
        distance: 18,
        angle: 20,
      },
      {
        x: 175,
        y: 42.5,
        xg: 0.45,
        player: 'Sidney Crosby',
        period: 3,
        time: '18:20',
        type: 'Backhand',
        distance: 8,
        angle: 5,
      },
    ]
  }
})

// Handle rink click
async function handleRinkClick(event: MouseEvent) {
  if (mode.value !== 'interactive') return

  const svg = event.currentTarget as SVGSVGElement // Change to SVGSVGElement
  const pt = svg.createSVGPoint()
  pt.x = event.clientX
  pt.y = event.clientY

  const svgP = pt.matrixTransform(svg.getScreenCTM()!.inverse())

  currentShot.value = { x: svgP.x, y: svgP.y }
  await predictXG()
}

// Handle shot click (NHL data mode)
function handleShotClick(shot: any) {
  selectedShot.value = shot
}

// Predict xG for current shot
async function predictXG() {
  if (!currentShot.value) return

  loading.value = true
  error.value = ''

  try {
    // Convert SVG coordinates to NHL coordinates
    const nhlCoords = svgToNhl(currentShot.value.x, currentShot.value.y, 200, 85)
    const metrics = calculateShotMetrics(nhlCoords.x, nhlCoords.y, true)

    const requestData = {
      arenaAdjustedShotDistance: metrics.distance,
      shotAngleAdjusted: metrics.angle,
      arenaAdjustedXCordABS: Math.abs(nhlCoords.x),
      arenaAdjustedYCordAbs: Math.abs(nhlCoords.y),
      xCord: nhlCoords.x,
      yCord: nhlCoords.y,
      shotType: shotType.value.toUpperCase(),
      shotRebound: isRebound.value ? 1 : 0,
      shotRush: isRush.value ? 1 : 0,
    }

    console.log('Sending:', requestData)

    const response = await axios.post('http://localhost:8000/predict/expected-goals', requestData)

    lastPrediction.value = response.data

    // Add shot to display
    interactiveShots.value.push({
      ...currentShot.value,
      xg: response.data.expected_goals,
      color: `hsl(${response.data.expected_goals * 120}, 100%, 50%)`,
    })
  } catch (err) {
    error.value = 'Error calculating xG'
    console.error(err)
  } finally {
    loading.value = false
  }
}

// Clear shots
function clearShots() {
  interactiveShots.value = []
  currentShot.value = null
  lastPrediction.value = null
  selectedShot.value = null
}

// Get shot quality based on xG
function getShotQuality(xg: number): string {
  if (xg > 0.2) return 'Excellent'
  if (xg > 0.12) return 'Good'
  if (xg > 0.08) return 'Average'
  return 'Poor'
}

function getShotQualityClass(xg: number): string {
  return getShotQuality(xg).toLowerCase()
}

function getRecommendation(xg: number): string {
  if (xg > 0.2) return 'High-danger chance! This shot location/type should be prioritized.'
  if (xg > 0.12) return 'Quality scoring chance. Continue creating these opportunities.'
  if (xg > 0.08) return 'Decent shot, but look for better positioning if possible.'
  return 'Low-percentage shot. Consider passing or improving position.'
}
</script>

<style scoped>
.rink-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

h2 {
  text-align: center;
  color: #333;
  margin-bottom: 20px;
}

.mode-selector {
  display: flex;
  gap: 20px;
  justify-content: center;
  margin-bottom: 20px;
}

.mode-selector label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.controls,
.nhl-controls {
  margin-bottom: 20px;
  display: flex;
  gap: 20px;
  align-items: center;
  flex-wrap: wrap;
  justify-content: center;
}

.controls label,
.nhl-controls label {
  display: flex;
  align-items: center;
  gap: 8px;
}

select {
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.clear-btn {
  padding: 6px 16px;
  background-color: #ff6b6b;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s;
}

.clear-btn:hover {
  background-color: #ff5252;
}

.prediction-result {
  margin-top: 20px;
  padding: 20px;
  background-color: #f5f5f5;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

h3 {
  margin-top: 0;
  color: #333;
}

.metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin: 15px 0;
}

.metric,
.detail {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.shot-details {
  margin: 15px 0;
  padding: 10px;
  background-color: #e8f4fd;
  border-radius: 4px;
}

.label {
  font-weight: 600;
  color: #666;
}

.value {
  font-size: 1.2em;
  font-weight: bold;
}

.value.excellent {
  color: #ff0000;
}
.value.good {
  color: #ff8800;
}
.value.average {
  color: #ffaa00;
}
.value.poor {
  color: #0088ff;
}

.shot-modifiers {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin: 10px 0;
}

.modifier {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: bold;
  background-color: #e0e0e0;
  color: #333;
}

.modifier.rebound {
  background-color: #ff6b6b;
  color: white;
}

.modifier.rush {
  background-color: #4ecdc4;
  color: white;
}

.recommendation {
  margin-top: 15px;
  padding: 10px;
  background-color: #e8f4fd;
  border-left: 4px solid #2196f3;
  border-radius: 4px;
}

.shooting-direction {
  text-align: center;
  color: #666;
  font-style: italic;
  margin: 10px 0;
}

.loading,
.error {
  margin-top: 20px;
  padding: 10px;
  text-align: center;
  border-radius: 4px;
}

.loading {
  background-color: #e3f2fd;
  color: #1976d2;
}

.error {
  background-color: #ffebee;
  color: #c62828;
}
</style>
