# Expanded xG Model Metrics - Complete Feature Set

## Overview
We've expanded from 8 basic features to **200+ comprehensive features** with **25+ player embeddings** capturing every nuance of NHL play.

## 1. Player Embeddings (25+ Roles)

### Core Roles
- **Shooter**: Shooting tendencies, hot zones, release patterns
- **Assist1**: Primary playmaking, vision, passing lanes created
- **Assist2**: Secondary support, cycle game contribution
- **Goalie**: Save patterns by zone, weaknesses, fatigue state
- **Defender1/2**: Defensive positioning, gap control, stick work

### Special Teams Roles
- **PP Quarterback**: Power play orchestration from point
- **PK Specialist**: Shot blocking, lane disruption
- **Faceoff Taker**: Possession starter
- **Screener**: Net-front presence, view obstruction
- **Net Presence**: Rebound conversion, tips, deflections

### Transition Roles
- **Zone Entry**: Controlled entries, speed, deception
- **Breakout**: First pass accuracy, outlet options

### On-Ice Context (All 11 players tracked)
- **Teammates 1-5**: Chemistry, support, spacing
- **Opponents 1-6**: Defensive structure, speed matching

## 2. Comprehensive Feature Categories (200+ Total)

### Shot Basics (15 features)
- Distance, angle, coordinates
- Shot type (7 variants including wraparound)
- Velocity estimate, one-timer flag, rebound flag

### Shooter Quality (30 features)
- Career: Goals, assists, shooting %, draft position
- Recent form: Last 5/10 games performance
- Shot patterns: Preferred locations, release types
- Clutch performance: OT goals, game-winners
- Physical: Height, weight, handedness, off-wing

### Goalie Vulnerability (25 features)
- Zone-specific save %: High/medium/low danger
- Weakness mapping: Glove, blocker, five-hole
- Current state: Shots faced, fatigue, confidence
- Situational: Screened, rush, cross-crease saves
- Recent performance: Last 10 shots faced

### On-Ice Context (40 features)
- Offensive unit: Combined WAR, chemistry, speed
- Defensive unit: Structure, gap control, experience
- Matchup advantages: Speed, size, skill, rest
- Special roles: Elite playmaker present, screener effectiveness
- Line matching: Top line vs bottom pair exploits

### Game State (20 features)
- Time: Period, elapsed, remaining, final minute
- Score: Differential, urgency index
- Situation: PP/PK/Empty net, zone time
- Pressure: Must-score scenarios

### Momentum (15 features)
- Recent goals, shot attempts, chances
- Momentum shifts, comeback probability
- Time since key events (goal, penalty, timeout)
- Consecutive offensive zone time

### Passing Sequence (20 features)
- Pass origin: Behind net, corner, point, slot
- Pass type: Royal road, cross-ice, drop pass
- Movement: East-west, north-south, defenders beaten
- Assist quality: Playmaking ratings, chemistry

### Defensive Structure (15 features)
- Pressure level, stick/body checks
- Formation: Box, diamond, man-to-man
- Breakdown indicators, odd-man situations
- Individual defense: Closest defender metrics

### Special Teams (10 features)
- PP formation, time elapsed, cross-ice availability
- PK structure, pressure type, clear attempts
- Personnel advantages

### Environmental (10 features)
- Home/away, arena factors, ice quality
- Schedule: Back-to-back, travel, timezone
- Fatigue indicators

## 3. Advanced Calculations

### Interaction Features
- **Shooter vs Goalie**: Historical matchup, style clash
- **Offensive vs Defensive Units**: Quality differential
- **Chemistry Scores**: Games together, success rate

### Composite Metrics
- **Shooting Talent**: Career goals above expected
- **Mismatch Score**: How badly defenders are outmatched
- **Fatigue Index**: Recent ice time and intensity
- **Clutch Factor**: Performance in high-leverage situations

## 4. Multi-Task Learning Outputs

Beyond just xG, the model predicts:
- **Rebound Probability**: Chance of a second chance
- **Rush Probability**: Fast break potential
- **High Danger Classification**: Shot quality tier
- **Fast Break Risk**: Chance of counter-attack

## 5. Attention Mechanisms

The model uses attention to:
- Weight which on-ice players matter most for this shot
- Identify key passing sequences
- Recognize defensive breakdowns
- Capture momentum shifts

## 6. Why This Matters

### Previous Models (MoneyPuck, etc.)
- ~20-30 features
- Basic shot location and type
- Limited player context
- No chemistry or momentum

### Our Model
- **200+ features** capturing every nuance
- **25+ player embeddings** for complete context
- **Attention mechanisms** for dynamic weighting
- **Multi-task learning** for richer predictions

### Expected Improvements
- **AUC**: 0.78+ (vs 0.72-0.75 for basic models)
- **Calibration**: Better probability estimates
- **Interpretability**: Know WHY a shot is dangerous
- **Real-time**: Fast inference for live games

## Implementation Status

✅ **Completed**:
- Comprehensive feature extraction (200+ features)
- Advanced player embeddings (25+ roles)
- Neural architecture with attention
- Multi-task learning framework

🔄 **In Progress**:
- Training on full NHL dataset
- Hyperparameter optimization
- Production deployment

🎯 **Next Steps**:
- A/B testing vs MoneyPuck
- Real-time integration
- Player development insights
- Team strategy recommendations

## The Bottom Line

This isn't just an incremental improvement - it's a complete reimagining of how we evaluate scoring chances. By capturing **every player, every tendency, every contextual factor**, we're building the most comprehensive xG model in hockey analytics.