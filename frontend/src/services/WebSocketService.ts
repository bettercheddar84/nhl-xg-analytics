// src/services/WebSocketService.ts
export class GameWebSocket {
  private ws: WebSocket | null = null
  private reconnectTimeout: number | null = null

  connect(
    gameId: string,
    handlers: {
      onShot?: (data: PredictionPayload) => void
      onError?: (error: string) => void
    },
  ) {
    this.ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}`)

    this.ws.onmessage = (event) => {
      const message: WSMessage = JSON.parse(event.data)

      switch (message.type) {
        case 'prediction':
          handlers.onShot?.(message.data as PredictionPayload)
          break
        case 'error':
          handlers.onError?.(message.data)
          break
      }
    }

    this.ws.onclose = () => this.handleReconnect(gameId, handlers)
  }

  private handleReconnect(...args: any[]) {
    this.reconnectTimeout = window.setTimeout(() => {
      this.connect(...args)
    }, 5000)
  }
}
