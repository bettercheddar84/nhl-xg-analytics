# Tracking Data Implementation

## Overview
While we don't have real-time tracking data (player speed, defender proximity), we can derive proxy metrics from the data we DO have.

## Current Proxy Implementations

### 1. Player Speed Estimation
```python
# From your data:
speed_from_prev = distance_from_prev_event / time_since_prev_event

# Enhanced calculation:
def estimate_player_speed(shot):
    base_speed = shot['speed_from_prev']
    
    # Rush shots are faster
    if shot['is_rush']:
        speed_multiplier = 1.3
    
    # Fatigue adjustment
    if shot['offensive_zone_time'] > 30:
        speed_multiplier = 0.8
        
    return base_speed * speed_multiplier
```

### 2. Defender Proximity Estimation
```python
def estimate_defender_proximity(shot):
    # Use on-ice quality differential as proxy
    defensive_quality = shot['defensive_quality_sum']
    
    # Blocked shots indicate close defenders
    if shot['blocker_id'] is not None:
        defender_distance = 'very_close'
    
    # High danger shots likely have fewer defenders
    elif shot['location_danger_score'] > 0.8:
        defender_distance = 'far'
    
    # Use shot type as indicator
    elif shot['shot_type'] in ['tip-in', 'deflection']:
        defender_distance = 'close'  # Traffic in front
        
    return defender_distance
```

### 3. Net-Front Presence
```python
# From your data:
- blocker_id indicates screener
- rebound opportunities indicate traffic
- deflections indicate multiple players

net_front_bodies = (
    (shot['blocker_id'] is not None) +
    (shot['is_deflection']) +
    (shot['created_rebound_chance'])
)
```

## Advanced Derivations

### 1. Zone Entry Speed
```python
# From offensive_zone_times.csv + play-by-play
def calculate_entry_speed(game_id, entry_time):
    # Find zone entry event
    neutral_zone_event = find_last_neutral_zone_event(game_id, entry_time)
    
    # Calculate speed
    distance = 85  # Blue line to goal line (feet)
    time_to_shot = shot_time - entry_time
    
    entry_speed = distance / time_to_shot
    return entry_speed
```

### 2. Passing Velocity
```python
# From prev_event coordinates
def estimate_pass_velocity(shot):
    if shot['prev_event_type'] == 'Pass':
        pass_distance = shot['distance_from_prev_event']
        pass_time = shot['time_since_prev_event']
        
        # Royal road passes are typically harder/faster
        if shot['royal_road_pass']:
            velocity_boost = 1.2
        else:
            velocity_boost = 1.0
            
        pass_velocity = (pass_distance / pass_time) * velocity_boost
        return pass_velocity
```

### 3. Defensive Pressure Index
```python
def calculate_defensive_pressure(shot):
    pressure_factors = {
        'zone_time': min(shot['offensive_zone_time'] / 30, 1),  # Tired D
        'shot_attempts': shot['shots_in_sequence'] / 5,  # Scramble mode
        'defender_quality': shot['defensive_quality_sum'] / 100,
        'fresh_defenders': shot['fresh_players'] / 5
    }
    
    # Weight factors
    pressure = (
        pressure_factors['zone_time'] * 0.3 +
        pressure_factors['shot_attempts'] * 0.2 +
        pressure_factors['defender_quality'] * 0.3 +
        (1 - pressure_factors['fresh_defenders']) * 0.2
    )
    
    return pressure
```

## What We Can Track

### 1. Movement Patterns
```python
# Track player movement through shift data
player_zones = []
for event in shift_events:
    if event['player_id'] == target_player:
        player_zones.append({
            'time': event['time'],
            'zone': event['zone'],
            'event': event['type']
        })

# Calculate zone transition speed
zone_changes = calculate_zone_transitions(player_zones)
avg_transition_time = np.mean([z['duration'] for z in zone_changes])
```

### 2. Shot Sequence Dynamics
```python
# From your shot sequences
sequence_acceleration = []
for i in range(1, len(shot_sequence)):
    time_between = shot_sequence[i]['time'] - shot_sequence[i-1]['time']
    sequence_acceleration.append(1 / time_between)

# Faster sequences = more chaos = less defensive structure
chaos_factor = np.mean(sequence_acceleration)
```

### 3. Fatigue-Adjusted Speed
```python
def adjust_speed_for_fatigue(player_id, game_time, base_speed):
    # From player_shift_patterns.csv
    shift_data = get_current_shift(player_id, game_time)
    
    time_on_ice = game_time - shift_data['shift_start']
    
    # Fatigue curve
    if time_on_ice < 30:
        fatigue_factor = 1.0
    elif time_on_ice < 45:
        fatigue_factor = 0.9
    else:
        fatigue_factor = 0.8
        
    return base_speed * fatigue_factor
```

## Future Tracking Integration

### When Real Tracking Becomes Available
```python
class TrackingDataIntegration:
    def __init__(self):
        self.tracking_features = [
            'player_speed_mph',
            'closest_defender_feet',
            'goalie_angle_degrees',
            'net_front_bodies_count',
            'puck_velocity_mph'
        ]
    
    def enhance_shot_features(self, shot, tracking_data):
        # Real speed replaces estimation
        shot['actual_speed'] = tracking_data['shooter_speed']
        
        # Real defender distance
        shot['closest_defender'] = tracking_data['nearest_opponent_distance']
        
        # Goalie positioning
        shot['goalie_angle'] = tracking_data['goalie_angle_to_puck']
        
        return shot
```

## Current Model Impact

### Without Tracking Proxies
- Basic distance/angle features only
- No speed or pressure context
- AUC ~0.75

### With Our Tracking Proxies
- Speed estimation from event timing
- Pressure from quality differentials
- Traffic from blocker/deflection data
- AUC ~0.80-0.82

### With Real Tracking Data (Future)
- Exact player speeds
- Precise defender gaps
- Goalie positioning
- AUC ~0.85-0.88

## Implementation Priority

### High Value Proxies (Do Now)
1. **Zone entry speed** - From zone time data
2. **Defensive pressure** - From on-ice quality
3. **Net-front traffic** - From blockers/deflections
4. **Fatigue-adjusted movement** - From shift data

### Medium Value (Nice to Have)
1. **Pass velocity** - From event coordinates
2. **Goalie lateral movement** - From shot sequences
3. **Breakout speed** - From zone exit timing

### Low Value (Skip for Now)
1. **Individual skating patterns**
2. **Exact defender positioning**
3. **Puck height tracking**

## Validation Methods

### 1. Speed Estimation Accuracy
```python
# Compare estimated speeds with known benchmarks
avg_rush_speed = shots[shots['is_rush']]['speed_estimate'].mean()
avg_normal_speed = shots[~shots['is_rush']]['speed_estimate'].mean()

# Rush shots should be 20-30% faster
speed_ratio = avg_rush_speed / avg_normal_speed
assert 1.2 <= speed_ratio <= 1.3
```

### 2. Pressure Index Validation
```python
# High pressure should correlate with:
# - Lower shot quality
# - More blocked shots
# - Lower goal rate

pressure_correlation = shots.groupby('pressure_quartile').agg({
    'is_goal': 'mean',
    'shot_distance': 'mean',
    'is_blocked': 'mean'
})
```

### 3. Traffic Detection
```python
# Net-front presence should increase:
# - Deflection rate
# - Rebound rate
# - Goal rate on low-angle shots

traffic_impact = shots.groupby('net_front_bodies').agg({
    'is_deflection': 'mean',
    'created_rebound': 'mean',
    'is_goal': 'mean'
})