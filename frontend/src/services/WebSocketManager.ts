// src/services/WebSocketManager.ts
class WebSocketManager {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private messageQueue: WebSocketMessage[] = []

  connect(gameId: string, handlers: MessageHandlers) {
    this.ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}`)

    this.ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data)
      this.routeMessage(message, handlers)
    }
  }

  private routeMessage(message: WebSocketMessage, handlers: MessageHandlers) {
    switch (message.type) {
      case 'shot':
        handlers.onShot?.(message.data as ShotEvent)
        break
      case 'prediction':
        handlers.onPrediction?.(message.data as PredictionPayload)
        break
    }
  }
}
