// src/stores/liveGameStore.ts
export const useLiveGameStore = defineStore('liveGame', () => {
  const shots = ref<ShotEvent[]>([])
  const predictions = ref<Map<string, PredictionPayload>>(new Map())
  const wsManager = new WebSocketManager()

  function connectToGame(gameId: string) {
    wsManager.connect(gameId, {
      onShot: (shot) => {
        shots.value.push(shot)
      },
      onPrediction: (prediction) => {
        predictions.value.set(prediction.shotId, prediction)
      },
    })
  }
})
