// src/types/game.ts
export interface GameEvent {
  eventType: 'shot' | 'goal' | 'penalty' | 'faceoff' | 'period_end'
  timestamp: number
  period: number
  timeRemaining: number
}

// Add these before ShotEvent interface:

export interface PlayerInfo {
  id: string
  name: string
  number: number
  position: 'C' | 'LW' | 'RW' | 'D' | 'G'
}

export interface RinkCoordinates {
  x: number // -100 to 100
  y: number // -42.5 to 42.5
}

export type ShotType =
  | 'Wrist'
  | 'Slap'
  | 'Snap'
  | 'Backhand'
  | 'Tip-In'
  | 'Deflection'
  | 'Wrap-Around'

// Fix the any type:
export interface WebSocketMessage {
  type: 'game_update' | 'shot' | 'prediction' | 'error'
  gameId: string
  data: ShotEvent | PredictionPayload | GameEvent | ErrorPayload
}

export interface ErrorPayload {
  message: string
  code?: string
}

export interface ShotEvent extends GameEvent {
  eventType: 'shot'
  shooter: PlayerInfo
  goalie: PlayerInfo
  location: RinkCoordinates
  shotType: ShotType
  result: 'goal' | 'save' | 'miss' | 'blocked'
  xG?: number
}

export interface WebSocketMessage {
  type: 'game_update' | 'shot' | 'prediction' | 'error'
  gameId: string
  data: any
}

export interface PredictionPayload {
  shotId: string
  xG: number
  factors: string[]
  timestamp: number
}
