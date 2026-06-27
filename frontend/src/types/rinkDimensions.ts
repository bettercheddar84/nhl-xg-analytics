// NHL Official Rink Dimensions and Specifications
export interface NHLRinkDimensions {
  // Official dimensions in feet
  length: 200 // 200 feet
  width: 85 // 85 feet

  // Zone dimensions
  neutralZoneLength: 50 // 50 feet (between blue lines)
  offensiveZoneLength: 75 // 75 feet (from blue line to end)

  // Line positions (from left end)
  goalLineDistance: 11 // 11 feet from end boards
  blueLinesFromCenter: 25 // 25 feet from center in each direction

  // Circle dimensions
  faceoffCircleRadius: 15 // 15 feet radius
  centerIceCircleRadius: 15 // 15 feet radius

  // Goal and crease
  goalWidth: 6 // 6 feet
  goalDepth: 4 // 4 feet
  creaseRadius: 6 // 6 feet radius

  // Dot positions
  faceoffDotFromEnd: 20 // 20 feet from end boards
  faceoffDotFromSide: 22 // 22 feet from side boards
}

export const NHL_RINK: NHLRinkDimensions = {
  length: 200,
  width: 85,
  neutralZoneLength: 50,
  offensiveZoneLength: 75,
  goalLineDistance: 11,
  blueLinesFromCenter: 25,
  faceoffCircleRadius: 15,
  centerIceCircleRadius: 15,
  goalWidth: 6,
  goalDepth: 4,
  creaseRadius: 6,
  faceoffDotFromEnd: 20,
  faceoffDotFromSide: 22,
}

// Convert real NHL coordinates to SVG coordinates
export function nhlToSvg(
  x: number,
  y: number,
  svgWidth: number,
  svgHeight: number,
): { x: number; y: number } {
  // NHL coordinate system: (0,0) is center ice
  // X: -100 to 100 (left to right)
  // Y: -42.5 to 42.5 (bottom to top)

  const svgX = ((x + 100) / 200) * svgWidth
  const svgY = ((42.5 - y) / 85) * svgHeight

  return { x: svgX, y: svgY }
}

// Convert SVG click to NHL coordinates
export function svgToNhl(
  svgX: number,
  svgY: number,
  svgWidth: number,
  svgHeight: number,
): { x: number; y: number } {
  const x = (svgX / svgWidth) * 200 - 100
  const y = 42.5 - (svgY / svgHeight) * 85

  return { x, y }
}

// Calculate shot metrics from NHL coordinates
export function calculateShotMetrics(
  x: number,
  y: number,
  shootingAtRightGoal: boolean = true,
): { distance: number; angle: number } {
  // Goal coordinates in NHL system
  const goalX = shootingAtRightGoal ? 89 : -89 // 11 feet from end (100-11)
  const goalY = 0 // Center of ice

  // Calculate distance
  const dx = goalX - x
  const dy = goalY - y
  const distance = Math.sqrt(dx * dx + dy * dy)

  // Calculate angle (0° is straight on)
  const angleRadians = Math.atan2(Math.abs(dy), Math.abs(dx))
  const angle = angleRadians * (180 / Math.PI)

  return { distance, angle }
}
