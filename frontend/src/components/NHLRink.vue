<template>
  <svg
    :width="width"
    :height="height"
    @click="$emit('rink-click', $event)"
    class="nhl-rink"
    viewBox="0 0 200 85"
  >
    <!-- Rink background -->
    <rect x="0" y="0" width="200" height="85" fill="#ffffff" stroke="#000" stroke-width="0.5" />

    <!-- End boards curves -->
    <path d="M 11 0 Q 0 0 0 11 L 0 74 Q 0 85 11 85" fill="none" stroke="#000" stroke-width="0.5" />
    <path
      d="M 189 0 Q 200 0 200 11 L 200 74 Q 200 85 189 85"
      fill="none"
      stroke="#000"
      stroke-width="0.5"
    />

    <!-- Center red line -->
    <line x1="100" y1="0" x2="100" y2="85" stroke="#ff0000" stroke-width="1" />

    <!-- Blue lines (25 feet from center = 75 and 125) -->
    <line x1="75" y1="0" x2="75" y2="85" stroke="#0033cc" stroke-width="1" />
    <line x1="125" y1="0" x2="125" y2="85" stroke="#0033cc" stroke-width="1" />

    <!-- Goal lines (11 feet from ends) -->
    <line x1="11" y1="0" x2="11" y2="85" stroke="#ff0000" stroke-width="0.5" />
    <line x1="189" y1="0" x2="189" y2="85" stroke="#ff0000" stroke-width="0.5" />

    <!-- Center ice circle -->
    <circle cx="100" cy="42.5" r="15" fill="none" stroke="#0033cc" stroke-width="0.5" />
    <circle cx="100" cy="42.5" r="0.5" fill="#0033cc" />

    <!-- Faceoff circles in zones -->
    <!-- Left zone -->
    <circle cx="31" cy="20.5" r="15" fill="none" stroke="#ff0000" stroke-width="0.5" />
    <circle cx="31" cy="64.5" r="15" fill="none" stroke="#ff0000" stroke-width="0.5" />
    <circle cx="31" cy="20.5" r="0.5" fill="#ff0000" />
    <circle cx="31" cy="64.5" r="0.5" fill="#ff0000" />

    <!-- Right zone -->
    <circle cx="169" cy="20.5" r="15" fill="none" stroke="#ff0000" stroke-width="0.5" />
    <circle cx="169" cy="64.5" r="15" fill="none" stroke="#ff0000" stroke-width="0.5" />
    <circle cx="169" cy="20.5" r="0.5" fill="#ff0000" />
    <circle cx="169" cy="64.5" r="0.5" fill="#ff0000" />

    <!-- Neutral zone dots -->
    <circle cx="75" cy="20.5" r="0.5" fill="#ff0000" />
    <circle cx="75" cy="64.5" r="0.5" fill="#ff0000" />
    <circle cx="125" cy="20.5" r="0.5" fill="#ff0000" />
    <circle cx="125" cy="64.5" r="0.5" fill="#ff0000" />

    <!-- Goals -->
    <!-- Left goal -->
    <rect x="9" y="39.5" width="2" height="6" fill="#ff0000" stroke="#000" stroke-width="0.2" />
    <!-- Right goal -->
    <rect x="189" y="39.5" width="2" height="6" fill="#ff0000" stroke="#000" stroke-width="0.2" />

    <!-- Goal creases -->
    <!-- Left crease -->
    <path d="M 11 36.5 A 6 6 0 0 0 11 48.5" fill="#e6f3ff" stroke="#ff0000" stroke-width="0.3" />
    <!-- Right crease -->
    <path d="M 189 36.5 A 6 6 0 0 1 189 48.5" fill="#e6f3ff" stroke="#ff0000" stroke-width="0.3" />

    <!-- Trapezoid behind goals -->
    <path d="M 11 31.5 L 8 28 L 8 57 L 11 53.5" fill="none" stroke="#ff0000" stroke-width="0.3" />
    <path
      d="M 189 31.5 L 192 28 L 192 57 L 189 53.5"
      fill="none"
      stroke="#ff0000"
      stroke-width="0.3"
    />

    <!-- Shot markers -->
    <g v-if="shots && shots.length > 0">
      <circle
        v-for="(shot, index) in shots"
        :key="index"
        :cx="shot.x"
        :cy="shot.y"
        r="1"
        :fill="getXGColor(shot.xg)"
        :opacity="shot === selectedShot ? 1 : 0.6"
        :stroke="shot === selectedShot ? '#000' : 'none'"
        stroke-width="0.3"
        @click.stop="$emit('shot-click', shot)"
        class="shot-marker"
      />
    </g>

    <!-- Current shot location -->
    <circle
      v-if="currentShot"
      :cx="currentShot.x"
      :cy="currentShot.y"
      r="1.5"
      :fill="getXGColor(currentShot.xg)"
      stroke="#000"
      stroke-width="0.3"
      class="current-shot"
    />
  </svg>
</template>

<script setup lang="ts">
interface Shot {
  x: number
  y: number
  xg?: number
  player?: string
  period?: number
  time?: string
  type?: string
}

interface Props {
  width?: number
  height?: number
  shots?: Shot[]
  currentShot?: Shot | null
  selectedShot?: Shot | null
}

const props = withDefaults(defineProps<Props>(), {
  width: 800,
  height: 340,
  shots: () => [],
  currentShot: null,
  selectedShot: null,
})

defineEmits<{
  'rink-click': [event: MouseEvent]
  'shot-click': [shot: Shot]
}>()

function getXGColor(xg: number | undefined): string {
  if (!xg) return '#cccccc'
  if (xg > 0.2) return '#ff0000' // Red - high danger
  if (xg > 0.12) return '#ff8800' // Orange - good chance
  if (xg > 0.08) return '#ffff00' // Yellow - average
  return '#0088ff' // Blue - low percentage
}
</script>

<style scoped>
.nhl-rink {
  border: 2px solid #000;
  cursor: crosshair;
  background-color: #f8f8f8;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.shot-marker {
  cursor: pointer;
  transition: all 0.2s;
}

.shot-marker:hover {
  r: 1.5;
}

.shot-stat {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
}

.stat-label {
  font-weight: bold;
}

.stat-value {
  color: #007bff;
}

.current-shot {
  animation: pulse 1s ease-in-out infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
  100% {
    opacity: 1;
  }
}
</style>
