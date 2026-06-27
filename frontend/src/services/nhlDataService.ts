// src/services/nhlDataService.ts (FIXED VERSION)

interface NHLShot {
  shooterName: string
  shooterPlayerId: number
  goalieNameForShot: string
  goalieIdForShot: number
  isGoal: number
  shotType: string
  shotDistance: number
  shotAngle: number
  xCordAdjusted: number
  yCordAdjusted: number
  xGoal: number
  period: number
  time: string
  homeTeamCode: string
  awayTeamCode: string
}

interface NHLGame {
  gameId: string
  date: string
  opponent: string
  result: string
}

class NHLDataService {
  // Fetch Penguins games
  async getPenguinsGames(season: string = '2023-24'): Promise<NHLGame[]> {
    console.log('Fetching games for season:', season)
    // This would connect to NHL API or your backend
    // For now, return sample data
    return [
      { gameId: '2023020001', date: '2023-10-10', opponent: 'CHI', result: 'W 4-2' },
      { gameId: '2023020002', date: '2023-10-12', opponent: 'DET', result: 'L 3-6' },
    ]
  }

  // Fetch shots for a specific game
  async getGameShots(gameId: string): Promise<NHLShot[]> {
    console.log('Fetching shots for game:', gameId)
    // This would fetch from NHL API
    // For demo, return sample shots
    return [
      {
        shooterName: 'Sidney Crosby',
        shooterPlayerId: 8471675,
        goalieNameForShot: 'Frederik Andersen',
        goalieIdForShot: 8475883,
        isGoal: 0,
        shotType: 'Wrist',
        shotDistance: 25,
        shotAngle: 15,
        xCordAdjusted: 65,
        yCordAdjusted: 10,
        xGoal: 0.125,
        period: 1,
        time: '5:23',
        homeTeamCode: 'PIT',
        awayTeamCode: 'CAR',
      },
    ]
  }

  // Convert NHL coordinates to our SVG coordinates
  convertNHLtoSVG(x: number, y: number): { x: number; y: number } {
    // NHL uses center ice as (0,0)
    // Our SVG uses (100, 42.5) as center
    return {
      x: x + 100,
      y: 42.5 - y, // Flip Y axis
    }
  }
}

export const nhlDataService = new NHLDataService()
