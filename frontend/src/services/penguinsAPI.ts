// src/services/penguinsAPI.ts

import axios from 'axios'

const API_BASE_URL = 'http://localhost:8000'

// Types for our API
export interface ShotData {
  shotDistance: number
  shotAngle: number
  shotType: string
  lastEventType: string
  timeSinceLast: number
  isRebound: number
  isRush: number
  period: number
}

export interface PredictionResponse {
  expected_goals: number
  shot_quality: string
  percentile: number
  recommendation: string
}

export interface ModelInfo {
  model_type: string
  accuracy: number
  auc_score: number
  n_features: number
  training_samples: number
  feature_categories: {
    numeric: string[]
    binary: string[]
    categorical: string[]
  }
  shot_types: string[]
  event_types: string[]
}

class PenguinsAPI {
  private axios = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
    },
  })

  // Get API health status
  async getHealth(): Promise<{ status: string; model_loaded: boolean }> {
    const response = await this.axios.get('/health')
    return response.data
  }

  // Get model information
  async getModelInfo(): Promise<ModelInfo> {
    const response = await this.axios.get('/model/info')
    return response.data
  }

  // Predict expected goals for a single shot
  async predictXG(shotData: ShotData): Promise<PredictionResponse> {
    const response = await this.axios.post('/predict/expected-goals', shotData)
    return response.data
  }

  // Predict expected goals for multiple shots
  async predictBatch(shots: ShotData[]): Promise<{
    predictions: PredictionResponse[]
    average_xg: number
    total_xg: number
  }> {
    const response = await this.axios.post('/predict/batch', shots)
    return response.data
  }
}

// Export singleton instance
export const penguinsAPI = new PenguinsAPI()

// Helper function to calculate shot distance and angle from coordinates
export function calculateShotMetrics(
  x: number,
  y: number,
  rinkWidth: number,
  rinkHeight: number,
  shootingAtRightGoal: boolean = true,
): { distance: number; angle: number } {
  // Goal coordinates
  const goalX = shootingAtRightGoal ? rinkWidth - 25 : 25
  const goalY = rinkHeight / 2

  // Calculate distance (scaled to feet)
  const dx = goalX - x
  const dy = goalY - y
  const distance = Math.sqrt(dx * dx + dy * dy) / 5

  // Calculate angle (in degrees)
  const angle = Math.atan2(dy, dx) * (180 / Math.PI)

  return { distance, angle }
}

// Helper to generate sample shot data for testing
export function generateSampleShots(count: number): ShotData[] {
  const shotTypes = ['Wrist', 'Slap', 'Snap', 'Backhand', 'Tip-In']
  const eventTypes = ['Pass', 'Carry', 'Rebound', 'Rush']

  return Array.from({ length: count }, () => ({
    shotDistance: Math.random() * 60 + 5,
    shotAngle: (Math.random() - 0.5) * 90,
    shotType: shotTypes[Math.floor(Math.random() * shotTypes.length)],
    lastEventType: eventTypes[Math.floor(Math.random() * eventTypes.length)],
    timeSinceLast: Math.random() * 20,
    isRebound: Math.random() > 0.85 ? 1 : 0,
    isRush: Math.random() > 0.7 ? 1 : 0,
    period: Math.floor(Math.random() * 3) + 1,
  }))
}
