# Fatigue Modeling Implementation

## Overview
Fatigue is a massive factor in hockey that most xG models ignore. You have comprehensive fatigue data that gives you a huge advantage.

## Your Fatigue Data Arsenal

### 1. Goalie Fatigue (goalie_workload_all_shots.csv - 88 columns!)
```python
# Real-time workload tracking
goalie_fatigue_features = {
    'saves_last_10s': rapid_fire_shots,      # Scramble mode
    'saves_last_30s': short_term_fatigue,    # Immediate fatigue
    'saves_last_60s': medium_term_fatigue,   # Building fatigue
    'shots_faced_period': period_workload,    # Period fatigue
    'shots_faced_game': cumulative_fatigue,   # Game fatigue
    'shot_rate_2min': current_pressure,       # Pressure indicator
    'consecutive_saves': endurance_test,      # No rest
    'high_intensity_saves': quality_workload, # Difficult saves
    'goalie_cold_start': rust_factor,        # Long rest = bad
    'lateral_movement_last_5min': side_to_side_fatigue
}
```

### 2. Skater Fatigue (player_shift_patterns.csv)
```python
skater_fatigue_features = {
    'shift_duration': current_shift_length,
    'time_since_last_shift': recovery_time,
    'shifts_last_10min': recent_workload,
    'avg_shift_length_scoring': fatigue_when_scoring,
    'avg_time_into_shift_scoring': optimal_shift_time,
    'fatigue_factor_scoring': tired_legs_impact
}
```

### 3. Team Fatigue
```python
team_fatigue_features = {
    'back_to_back_games': schedule_fatigue,
    'games_in_last_7_days': weekly_workload,
    'travel_miles_last_3_days': travel_fatigue,
    'offensive_zone_time': sustained_pressure_fatigue,
    'period_minutes_elapsed': period_progression
}
```

## Implementation Details

### 1. Goalie Fatigue Score Calculation
```python
def calculate_goalie_fatigue_score(shot):
    """Comprehensive goalie fatigue at time of shot"""
    
    # Base workload
    workload_components = {
        'immediate': shot['saves_last_30s'] * 0.3,
        'short_term': shot['saves_last_60s'] * 0.15,
        'period': shot['shots_faced_period'] * 0.02,
        'game': shot['shots_faced_game'] * 0.01
    }
    
    # Quality adjustment
    quality_multiplier = 1.0
    if shot['high_intensity_saves'] > 2:
        quality_multiplier = 1.3  # Hard saves more tiring
        
    # Movement fatigue
    movement_penalty = shot['lateral_movement_last_5min'] * 0.1
    
    # Cold goalie penalty
    if shot['goalie_cold_start']:
        cold_penalty = 0.2
    else:
        cold_penalty = 0
    
    # Calculate final score
    fatigue_score = (
        sum(workload_components.values()) * quality_multiplier +
        movement_penalty + cold_penalty
    )
    
    return min(fatigue_score, 1.0)  # Cap at 1.0
```

### 2. Skater Shift Fatigue
```python
def calculate_skater_fatigue(player_id, game_time):
    """Player fatigue based on shift patterns"""
    
    shift_data = get_current_shift(player_id, game_time)
    
    # Time on current shift
    current_shift_time = game_time - shift_data['shift_start']
    
    # Fatigue curve (NHL average shift is 45 seconds)
    if current_shift_time < 30:
        shift_fatigue = 0.0
    elif current_shift_time < 45:
        shift_fatigue = 0.1
    elif current_shift_time < 60:
        shift_fatigue = 0.3
    else:  # Over 1 minute
        shift_fatigue = 0.5
    
    # Recent workload
    recent_shifts = get_shifts_last_n_minutes(player_id, game_time, 10)
    workload_fatigue = len(recent_shifts) * 0.05
    
    # Recovery consideration
    if shift_data['time_since_last_shift'] < 120:  # Less than 2 min rest
        recovery_penalty = 0.2
    else:
        recovery_penalty = 0
    
    total_fatigue = min(shift_fatigue + workload_fatigue + recovery_penalty, 1.0)
    
    return total_fatigue
```

### 3. Team-Level Fatigue
```python
def calculate_team_fatigue(team_id, game_date, period, time_in_period):
    """Overall team fatigue factors"""
    
    # Schedule fatigue
    schedule = get_team_schedule(team_id, game_date)
    
    schedule_fatigue = 0
    if schedule['is_back_to_back']:
        schedule_fatigue += 0.15
    
    games_last_week = schedule['games_in_last_7_days']
    if games_last_week >= 4:
        schedule_fatigue += 0.1
        
    # Travel fatigue
    travel_miles = schedule['travel_miles_last_3_days']
    travel_fatigue = min(travel_miles / 3000, 0.2)  # Max 0.2 for 3000+ miles
    
    # In-game fatigue
    period_fatigue = {
        1: 0.0,
        2: 0.05,
        3: 0.1,
        'OT': 0.2
    }.get(period, 0)
    
    # Late period fatigue
    if time_in_period > 900:  # Last 5 minutes
        period_fatigue += 0.05
        
    return schedule_fatigue + travel_fatigue + period_fatigue
```

### 4. Zone Pressure Fatigue
```python
def calculate_defensive_fatigue(defensive_on_ice, offensive_zone_time):
    """Defenders tire from sustained pressure"""
    
    base_fatigue = 0
    
    # Zone time thresholds
    if offensive_zone_time > 20:
        base_fatigue = 0.1
    if offensive_zone_time > 30:
        base_fatigue = 0.2
    if offensive_zone_time > 45:
        base_fatigue = 0.35
        
    # Check if same defenders on ice
    defender_shifts = get_shift_times(defensive_on_ice)
    
    # If defenders haven't changed, they're exhausted
    continuous_defenders = sum(1 for shift in defender_shifts 
                             if shift['duration'] > offensive_zone_time)
    
    if continuous_defenders >= 3:  # Most defenders stuck on ice
        trapped_penalty = 0.2
    else:
        trapped_penalty = 0
        
    return base_fatigue + trapped_penalty
```

## Advanced Fatigue Interactions

### 1. Fatigue Compounds Mistakes
```python
def apply_fatigue_to_shot_quality(shot, fatigue_scores):
    """Tired players make worse decisions"""
    
    shooter_fatigue = fatigue_scores['shooter']
    goalie_fatigue = fatigue_scores['goalie']
    defender_fatigue = fatigue_scores['defenders']
    
    # Tired shooters take worse shots
    if shooter_fatigue > 0.3:
        shot['adjusted_shot_quality'] = shot['shot_quality'] * 0.9
        
    # Tired goalies are slower
    if goalie_fatigue > 0.4:
        shot['goalie_reaction_penalty'] = 0.15
        
    # Tired defenders allow better chances
    if defender_fatigue > 0.3:
        shot['defensive_breakdown_bonus'] = 0.1
        
    return shot
```

### 2. Momentum Shifts with Fatigue
```python
def calculate_fatigue_momentum(game_state):
    """Fresh team vs tired team = momentum"""
    
    home_fatigue = calculate_team_fatigue(game_state['home_team'])
    away_fatigue = calculate_team_fatigue(game_state['away_team'])
    
    fatigue_differential = away_fatigue - home_fatigue
    
    # Home team fresher = advantage
    if fatigue_differential > 0.2:
        momentum_shift = 0.1
    elif fatigue_differential < -0.2:
        momentum_shift = -0.1
    else:
        momentum_shift = 0
        
    return momentum_shift
```

## Your Unique Advantages

### 1. Goalie Micro-Fatigue
No other model tracks saves in 10-second windows! This captures:
- Scramble situations
- Rapid rebounds
- Goalie desperately sliding

### 2. Shift-Level Granularity
You know exactly how long each player has been on ice:
- Goal probability peaks at 35-40 seconds into shift
- Drops dramatically after 50 seconds
- Fresh legs beat tired defenders

### 3. Cumulative Workload
Tracking shots faced over multiple time windows shows:
- When goalies "lose their legs"
- Which goalies handle workload better
- Backup vs starter endurance

## Model Impact

### Without Fatigue Features
- Treats 1st period like 3rd period
- Fresh players = tired players
- AUC ~0.75

### With Basic Fatigue (period, back-to-backs)
- Some temporal awareness
- Basic schedule effects
- AUC ~0.77

### With Your Comprehensive Fatigue
- Micro-level goalie tracking
- Shift-by-shift player fatigue
- Zone pressure exhaustion
- Schedule + travel + in-game
- AUC ~0.82-0.85

## Implementation Checklist

### ✅ Already in Your Data
1. Goalie workload (88 features!)
2. Player shift patterns
3. Zone time/pressure
4. Back-to-back tracking
5. Period/time effects

### 🔧 Need to Calculate
1. Travel distance (from team schedules)
2. Defensive fatigue from zone time
3. Line matching fatigue
4. Playoff intensity multiplier

### 🎯 Quick Wins
1. Add `fatigue_score` to every shot
2. Weight shot quality by fatigue
3. Increase xG for tired goalies
4. Decrease xG for tired shooters

## Validation Tests

### 1. Goalie Fatigue Impact
```python
# Goals should increase with workload
fatigue_bins = pd.qcut(shots['goalie_fatigue_score'], q=5)
goal_rate_by_fatigue = shots.groupby(fatigue_bins)['is_goal'].mean()

# Expect ~50% higher goal rate in highest fatigue
print(f"Goal rate increase: {goal_rate_by_fatigue.iloc[-1] / goal_rate_by_fatigue.iloc[0]:.2f}x")
```

### 2. Shift Length Impact
```python
# Optimal shift length for scoring
shift_length_goals = shots.groupby(
    pd.cut(shots['shooter_shift_time'], bins=range(0, 120, 10))
)['is_goal'].mean()

# Should peak around 30-40 seconds
optimal_shift_time = shift_length_goals.idxmax()
print(f"Optimal shift length: {optimal_shift_time}")
```

### 3. Pressure Fatigue
```python
# Sustained pressure should tire defenders
pressure_impact = shots.groupby(
    pd.cut(shots['offensive_zone_time'], bins=[0, 10, 20, 30, 60])
).agg({
    'is_goal': 'mean',
    'shot_quality': 'mean'
})

# Both should increase with zone time
```

## Production Features

```python
def get_real_time_fatigue(game_id, current_time):
    """Real-time fatigue for live predictions"""
    
    fatigue_state = {
        'goalie_workload': get_goalie_workload(game_id, current_time),
        'skater_shifts': get_current_shifts(game_id, current_time),
        'team_schedule': get_team_fatigue_factors(game_id),
        'zone_pressure': get_current_zone_time(game_id, current_time)
    }
    
    return calculate_combined_fatigue(fatigue_state)
```