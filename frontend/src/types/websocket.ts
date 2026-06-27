// src/types/websocket.ts
export interface WSMessage<T = any> {
  type: 'shot' | 'goal' | 'prediction' | 'game_update' | 'error'
  timestamp: number
  gameId: string
  data: T
}

export interface ShotPayload {
  shotId: string
  shooter: { id: number; name: string }
  goalie: { id: number; name: string }
  location: { x: number; y: number }
  shotType: string
  period: number
  time: string
  features: {
    distance: number
    angle: number
    timeSinceFaceoff: number
    isOffZoneFaceoff: boolean
    shooterTalent: number
    goalieSavePct: number
  }
}

export interface PredictionPayload extends ShotPayload {
  xG: number
  factors: string[]
  percentile: number
}
