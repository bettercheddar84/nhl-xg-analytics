# Puck Movement & Pre-Shot Sequences

## Overview
Pre-shot puck movement is crucial for xG. Quick passing, royal road passes, and zone entries dramatically affect goal probability.

## Current Implementation

### 1. Passing Sequences (from goal_sequences_fixed.csv)
```python
# Available data:
- assist1_id, assist2_id: Who touched puck before goal
- sequence_duration: Time from sequence start to goal
- offensive_zone_events: Number of events in O-zone
- shots_before_goal: Shot attempts in sequence
- quick_strike: Boolean for rapid goals
- sustained_pressure: Extended zone time
```

### 2. Royal Road Pass Detection
```python
def detect_royal_road_pass(shot):
    """Pass that crosses slot laterally - most dangerous pass in hockey"""
    
    # From your implementation
    royal_road = (
        (shot['prev_event_x'] * shot['x_coord'] < 0) &  # Opposite sides
        (abs(shot['prev_event_y']) < 20) &  # Through slot
        (shot['prev_event_type'] == 'Pass')
    )
    
    # Enhanced version with quality scoring
    if royal_road:
        # Calculate pass quality
        pass_distance = abs(shot['prev_event_x'] - shot['x_coord'])
        pass_speed = pass_distance / shot['time_since_prev_event']
        
        # Faster passes are harder to defend
        if pass_speed > 50:  # ft/second
            royal_road_quality = 1.0
        else:
            royal_road_quality = 0.7
            
    return royal_road, royal_road_quality
```

### 3. Zone Entry Analysis
```python
# From offensive_zone_times.csv + play-by-play
def analyze_zone_entry(game_id, shot_time):
    zone_data = offensive_zone_times[
        (offensive_zone_times['game_id'] == game_id) &
        (offensive_zone_times['time'] <= shot_time)
    ].iloc[-1]
    
    entry_types = {
        'controlled': 1.0,   # Carry in
        'dump_chase': 0.5,   # Dump and chase
        'neutral_zone': 0.7  # Off turnover
    }
    
    # From your data
    time_since_entry = shot_time - zone_data['entry_time']
    entry_quality = entry_types.get(zone_data['entry_type'], 0.5)
    
    return {
        'zone_time': time_since_entry,
        'entry_quality': entry_quality,
        'fresh_attack': time_since_entry < 5
    }
```

### 4. Passing Network Features
```python
# From passing_sequences.csv
def extract_passing_features(sequence_id):
    sequence = passing_sequences[passing_sequences['sequence_id'] == sequence_id]
    
    features = {
        'num_passes': sequence['num_passes'],
        'unique_players': sequence['num_players'],
        'royal_road_passes': sequence['royal_road_passes'],
        'pass_velocity': sequence['total_pass_distance'] / sequence['duration'],
        'ended_in_shot': sequence['ended_in_shot'],
        'danger_score': sequence['sequence_danger_score']
    }
    
    # Add passing patterns
    if features['num_passes'] >= 3:
        features['tic_tac_toe'] = True  # Classic 3-pass play
    
    if features['royal_road_passes'] > 0:
        features['cross_slot_play'] = True
        
    return features
```

## Advanced Sequence Analysis

### 1. Pre-Shot Movement Patterns
```python
def analyze_pre_shot_movement(shot_data, window=10):
    """Track puck movement in 10 seconds before shot"""
    
    events = get_events_before_shot(shot_data, window)
    
    movement_metrics = {
        'total_distance': 0,
        'direction_changes': 0,
        'vertical_movement': 0,
        'horizontal_movement': 0,
        'towards_net_movement': 0
    }
    
    for i in range(1, len(events)):
        prev = events[i-1]
        curr = events[i]
        
        # Calculate movement
        dx = curr['x'] - prev['x']
        dy = curr['y'] - prev['y']
        distance = np.sqrt(dx**2 + dy**2)
        
        movement_metrics['total_distance'] += distance
        movement_metrics['horizontal_movement'] += abs(dx)
        movement_metrics['vertical_movement'] += abs(dy)
        
        # Check if moving towards net
        if curr['x'] > prev['x']:  # Assuming right-side attack
            movement_metrics['towards_net_movement'] += dx
            
        # Direction changes (east-west movement)
        if i > 1:
            prev_direction = np.sign(events[i-1]['x'] - events[i-2]['x'])
            curr_direction = np.sign(dx)
            if prev_direction != curr_direction:
                movement_metrics['direction_changes'] += 1
    
    # Derive advanced features
    movement_metrics['east_west_ratio'] = (
        movement_metrics['horizontal_movement'] / 
        (movement_metrics['vertical_movement'] + 1)
    )
    
    movement_metrics['puck_speed'] = (
        movement_metrics['total_distance'] / window
    )
    
    return movement_metrics
```

### 2. Passing Combo Analysis
```python
# From training_assists_simplified.csv
def analyze_passing_combos(shot):
    """D-F-F is different from F-F-F"""
    
    combo = shot['passing_combo']  # e.g., "D-R-C"
    
    combo_values = {
        'D-D-F': 0.8,   # Point shot setup
        'D-F-F': 1.0,   # Classic breakout
        'F-F-F': 1.2,   # Forwards cycling
        'F-D-F': 0.9,   # Using point man
        'C-W-C': 1.3,   # Cross-ice play
    }
    
    # Position-specific boost
    if 'C' in combo:  # Center involved
        playmaking_boost = 1.1
    else:
        playmaking_boost = 1.0
        
    combo_quality = combo_values.get(combo, 0.8) * playmaking_boost
    
    return combo_quality
```

### 3. Sequence Momentum
```python
def calculate_sequence_momentum(events):
    """Measure if attack is accelerating"""
    
    event_times = [e['time'] for e in events]
    
    # Calculate time between events
    intervals = np.diff(event_times)
    
    # Decreasing intervals = accelerating play
    if len(intervals) > 2:
        acceleration = -np.polyfit(range(len(intervals)), intervals, 1)[0]
    else:
        acceleration = 0
        
    momentum_features = {
        'acceleration': acceleration,
        'avg_interval': np.mean(intervals),
        'chaos_factor': np.std(intervals),
        'building_pressure': acceleration > 0.1
    }
    
    return momentum_features
```

## Unique Insights from Your Data

### 1. Shot Assist Quality
```python
# You have assist1_id and assist2_id for every shot
def score_assist_quality(shot):
    if pd.isna(shot['assist1_id']):
        return 0
    
    # Get assistant's passing stats
    assist1_stats = skaters[skaters['playerId'] == shot['assist1_id']]
    
    if not assist1_stats.empty:
        # Primary assist quality
        primary_quality = (
            assist1_stats['I_F_primaryAssists'].iloc[0] / 
            assist1_stats['games_played'].iloc[0]
        )
        
        # Royal road tendency
        royal_road_rate = (
            shots[(shots['assist1_id'] == shot['assist1_id']) & 
                  shots['royal_road_pass']].shape[0] /
            shots[shots['assist1_id'] == shot['assist1_id']].shape[0]
        )
        
        assist_quality = primary_quality + royal_road_rate
    else:
        assist_quality = 0.5  # Default
        
    return assist_quality
```

### 2. Zone Entry Patterns
```python
# Combine offensive_zone_times.csv with shift data
def analyze_entry_patterns(team, game_id):
    entries = offensive_zone_times[
        (offensive_zone_times['game_id'] == game_id) &
        (offensive_zone_times['team'] == team)
    ]
    
    patterns = {
        'rush_entries': (entries['duration'] < 5).sum(),
        'sustained_entries': (entries['duration'] > 20).sum(),
        'failed_entries': (entries['shots_during'] == 0).sum(),
        'high_danger_entries': (entries['goals_during'] > 0).sum()
    }
    
    # Entry success rate
    patterns['entry_success_rate'] = (
        patterns['sustained_entries'] / len(entries)
    )
    
    return patterns
```

### 3. Faceoff-to-Shot Sequences
```python
# You track time_since_faceoff and off_faceoff
def analyze_faceoff_plays(shot):
    if not shot['off_faceoff']:
        return None
        
    faceoff_features = {
        'quick_strike': shot['time_since_faceoff'] < 3,
        'set_play': 3 <= shot['time_since_faceoff'] <= 10,
        'extended_possession': shot['time_since_faceoff'] > 10
    }
    
    # Faceoff location matters
    if shot['faceoff_zone'] == 'O':  # Offensive zone
        faceoff_features['danger_multiplier'] = 1.3
    else:
        faceoff_features['danger_multiplier'] = 1.0
        
    return faceoff_features
```

## Impact on xG Model

### Without Puck Movement Features
- Static shot location only
- No context of how puck arrived
- AUC ~0.72

### With Basic Movement (current)
- Royal road pass detection
- Zone time before shot
- Basic sequence tracking
- AUC ~0.78

### With Advanced Movement
- Full passing networks
- Entry quality scoring
- Momentum calculation
- Assist quality ratings
- AUC ~0.82-0.84

## Implementation Priority

### Must Have (Immediate Impact)
1. **Royal road pass** - Already implemented
2. **Zone time** - In offensive_zone_times.csv
3. **Assist quality** - From skaters.csv stats
4. **Quick strike** - In goal_sequences_fixed.csv

### Should Have (Moderate Impact)
1. **Passing combos** - In training_assists_simplified.csv
2. **Entry patterns** - Derive from zone times
3. **Sequence momentum** - Calculate from events
4. **Faceoff plays** - Already tracked

### Nice to Have (Marginal Gains)
1. **Full passing networks**
2. **Puck speed estimation**
3. **Defensive formation breaking**

## Validation

### Test Royal Road Impact
```python
# Royal road passes should 2-3x goal probability
rr_goal_rate = shots[shots['royal_road_pass']]['is_goal'].mean()
normal_goal_rate = shots[~shots['royal_road_pass']]['is_goal'].mean()

print(f"Royal Road lift: {rr_goal_rate / normal_goal_rate:.2f}x")
```

### Verify Zone Time Effect
```python
# Longer zone time = tired defenders = higher goals
zone_time_impact = shots.groupby(pd.cut(shots['offensive_zone_time'], bins=5)).agg({
    'is_goal': 'mean',
    'shot_distance': 'mean'
})

# Should see increasing goal rate with zone time
```

### Passing Combo Analysis
```python
# Different passing patterns, different success
combo_success = shots.groupby('passing_combo').agg({
    'is_goal': ['mean', 'count'],
    'royal_road_pass': 'mean'
}).sort_values(('is_goal', 'mean'), ascending=False)

print("Top 10 passing combinations:")
print(combo_success.head(10))
```