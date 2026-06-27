# Goalie-Specific Models Implementation

## Overview
Different goalies have different strengths. Your model should know that Vasilevskiy handles lateral movement better than most, or that some goalies struggle with high shots.

## Your Goalie Data

### 1. Individual Goalie Stats (goalies.csv)
```python
goalie_features = {
    'xGoals': expected_goals_against,
    'goals': actual_goals_against,
    'GSAx': goals_saved_above_expected,  # Key quality metric
    'lowDangerSV%': save_pct_low_danger,
    'mediumDangerSV%': save_pct_medium_danger,
    'highDangerSV%': save_pct_high_danger,
    'RBS': rebounds_created,
    'RBSV%': rebound_save_percentage
}
```

### 2. Workload Patterns (goalie_workload_all_shots.csv)
```python
workload_patterns = {
    'save_pct_last_10': recent_performance,
    'high_danger_save_pct': quality_performance,
    'goalie_quality_rating': overall_rating,
    'consecutive_saves': hot_hand_indicator,
    'fatigue_score': endurance_metric
}
```

### 3. Goalie-Specific Tendencies
```python
# Derive from shot-level data
def calculate_goalie_tendencies(goalie_id):
    goalie_shots = shots[shots['goalie_id'] == goalie_id]
    
    tendencies = {
        'glove_side_sv%': goalie_shots[goalie_shots['y_coord'] > 0]['is_goal'].mean(),
        'blocker_side_sv%': goalie_shots[goalie_shots['y_coord'] < 0]['is_goal'].mean(),
        'five_hole_vulnerability': goalie_shots[goalie_shots['shot_type'] == 'backhand']['is_goal'].mean(),
        'wraparound_sv%': goalie_shots[goalie_shots['is_wraparound']]['is_goal'].mean(),
        'screened_shot_sv%': goalie_shots[goalie_shots['blocker_id'].notna()]['is_goal'].mean()
    }
    
    return tendencies
```

## Implementation Strategies

### 1. Hierarchical Goalie Model
```python
class GoalieSpecificXG:
    def __init__(self):
        self.base_model = load_base_xg_model()
        self.goalie_adjustments = {}
        
    def train_goalie_adjustments(self, shots_df):
        """Train goalie-specific adjustments"""
        
        for goalie_id in shots_df['goalie_id'].unique():
            goalie_shots = shots_df[shots_df['goalie_id'] == goalie_id]
            
            if len(goalie_shots) < 500:  # Need sufficient sample
                continue
                
            # Get base predictions
            base_xg = self.base_model.predict(goalie_shots)
            
            # Calculate goalie-specific residuals
            residuals = goalie_shots['is_goal'] - base_xg
            
            # Train adjustment model
            adjustment_features = self._extract_goalie_features(goalie_shots)
            adjustment_model = train_residual_model(adjustment_features, residuals)
            
            self.goalie_adjustments[goalie_id] = adjustment_model
            
    def predict(self, shot):
        """Predict with goalie adjustment"""
        base_xg = self.base_model.predict(shot)
        
        if shot['goalie_id'] in self.goalie_adjustments:
            adjustment = self.goalie_adjustments[shot['goalie_id']].predict(shot)
            final_xg = base_xg + adjustment
        else:
            # Use average goalie adjustment
            final_xg = base_xg * self._get_goalie_quality_multiplier(shot['goalie_id'])
            
        return np.clip(final_xg, 0, 1)
```

### 2. Goalie Embeddings
```python
def create_goalie_embedding(goalie_id):
    """Create embedding capturing goalie style"""
    
    # Base stats from goalies.csv
    goalie_stats = goalies[goalies['playerId'] == goalie_id]
    
    if goalie_stats.empty:
        return np.zeros(16)  # Default embedding
        
    # Performance metrics
    performance_features = [
        goalie_stats['GSAx'].iloc[0],  # Quality metric
        goalie_stats['lowDangerSV%'].iloc[0],
        goalie_stats['mediumDangerSV%'].iloc[0],
        goalie_stats['highDangerSV%'].iloc[0],
    ]
    
    # Style metrics
    style_features = [
        goalie_stats['rebounds'].iloc[0] / goalie_stats['unblocked_shot_attempts'].iloc[0],  # Rebound control
        goalie_stats['freeze'].iloc[0] / goalie_stats['unblocked_shot_attempts'].iloc[0],     # Puck freezing tendency
    ]
    
    # Workload handling
    workload_data = goalie_workload[goalie_workload['goalie_id'] == goalie_id]
    if not workload_data.empty:
        workload_features = [
            workload_data['fatigue_score'].mean(),  # Average fatigue
            workload_data['save_pct_last_10'].std(),  # Consistency
        ]
    else:
        workload_features = [0.5, 0.1]
        
    # Physical attributes (if available)
    physical_features = get_goalie_physical_attributes(goalie_id)
    
    # Combine all features
    embedding = np.concatenate([
        normalize(performance_features),
        normalize(style_features),
        normalize(workload_features),
        normalize(physical_features)
    ])
    
    return embedding
```

### 3. Situation-Specific Goalie Performance
```python
def get_goalie_situational_adjustment(goalie_id, shot_context):
    """Some goalies better in certain situations"""
    
    adjustments = {}
    
    # Breakaway/penalty shot specialist?
    if shot_context['is_penalty_shot'] or shot_context['is_breakaway']:
        breakaway_stats = get_goalie_breakaway_stats(goalie_id)
        adjustments['breakaway'] = breakaway_stats['save_pct'] - league_avg_breakaway
        
    # Scramble/rebound control
    if shot_context['is_rebound']:
        rebound_stats = get_goalie_rebound_stats(goalie_id)
        adjustments['rebound'] = rebound_stats['second_save_pct'] - league_avg_rebound
        
    # Screened shot handling
    if shot_context['blocker_id'] is not None:
        screen_stats = get_goalie_screen_stats(goalie_id)
        adjustments['screened'] = screen_stats['screened_sv_pct'] - league_avg_screened
        
    # Power play specialist
    if shot_context['is_powerplay']:
        pp_stats = get_goalie_special_teams_stats(goalie_id)
        adjustments['powerplay'] = pp_stats['pp_sv_pct'] - league_avg_pp
        
    return sum(adjustments.values())
```

### 4. Goalie Matchup History
```python
def get_shooter_vs_goalie_history(shooter_id, goalie_id):
    """Some shooters own certain goalies"""
    
    matchup_shots = shots[
        (shots['shooter_id'] == shooter_id) & 
        (shots['goalie_id'] == goalie_id)
    ]
    
    if len(matchup_shots) < 10:  # Need sufficient history
        return 0
        
    matchup_stats = {
        'goals': matchup_shots['is_goal'].sum(),
        'shots': len(matchup_shots),
        'shooting_pct': matchup_shots['is_goal'].mean(),
        'avg_xg': matchup_shots['xG'].mean() if 'xG' in matchup_shots else None
    }
    
    # Compare to shooter's average
    shooter_avg = shots[shots['shooter_id'] == shooter_id]['is_goal'].mean()
    
    # Positive = shooter has goalie's number
    matchup_advantage = matchup_stats['shooting_pct'] - shooter_avg
    
    # Weight by sample size (more history = more confident)
    confidence = min(len(matchup_shots) / 50, 1.0)
    
    return matchup_advantage * confidence
```

## Advanced Goalie Features

### 1. Movement Pattern Vulnerability
```python
def analyze_goalie_movement_patterns(goalie_id):
    """Some goalies struggle with lateral movement"""
    
    goalie_shots = shots[shots['goalie_id'] == goalie_id]
    
    # Lateral movement shots (royal road passes, cross-crease)
    lateral_shots = goalie_shots[
        goalie_shots['royal_road_pass'] | 
        (goalie_shots['prev_event_y'] * goalie_shots['y_coord'] < 0)
    ]
    
    movement_vulnerability = {
        'lateral_sv_pct': 1 - lateral_shots['is_goal'].mean(),
        'lateral_shots_faced': len(lateral_shots),
        'recovery_time_needed': lateral_shots['time_since_prev_event'].mean()
    }
    
    # Compare to league average
    league_lateral_sv_pct = 0.88  # Example
    movement_vulnerability['vs_league'] = (
        movement_vulnerability['lateral_sv_pct'] - league_lateral_sv_pct
    )
    
    return movement_vulnerability
```

### 2. Fatigue Response Profiles
```python
def analyze_goalie_fatigue_response(goalie_id):
    """How does this goalie handle workload?"""
    
    workload_data = goalie_workload[goalie_workload['goalie_id'] == goalie_id]
    
    # Performance degradation with fatigue
    fatigue_bins = pd.qcut(workload_data['fatigue_score'], q=5)
    
    fatigue_profile = workload_data.groupby(fatigue_bins).agg({
        'is_goal': 'mean',
        'save_pct_last_10': 'mean',
        'high_danger_save_pct': 'mean'
    })
    
    # Calculate degradation rate
    fresh_performance = fatigue_profile.iloc[0]['is_goal']
    tired_performance = fatigue_profile.iloc[-1]['is_goal']
    
    degradation_rate = (tired_performance - fresh_performance) / fresh_performance
    
    # Some goalies are "workhorses" - handle fatigue better
    if degradation_rate < 0.1:
        goalie_type = 'workhorse'
    elif degradation_rate > 0.3:
        goalie_type = 'needs_rest'
    else:
        goalie_type = 'average_endurance'
        
    return {
        'goalie_type': goalie_type,
        'degradation_rate': degradation_rate,
        'optimal_shot_range': (20, 30)  # Shots per game
    }
```

### 3. Hot/Cold Streaks
```python
def get_goalie_current_form(goalie_id, game_date, window=10):
    """Recent performance matters"""
    
    recent_games = get_last_n_games(goalie_id, game_date, n=window)
    
    if not recent_games:
        return 0
        
    recent_stats = {
        'save_pct': recent_games['saves'].sum() / recent_games['shots'].sum(),
        'gsax_per_game': recent_games['GSAx'].mean(),
        'quality_starts': (recent_games['save_pct'] > 0.920).sum()
    }
    
    # Compare to season average
    season_avg = get_season_stats(goalie_id)
    
    form_score = (
        (recent_stats['save_pct'] - season_avg['save_pct']) * 100 +
        (recent_stats['gsax_per_game'] - season_avg['gsax_per_game']) * 0.5
    )
    
    if form_score > 2:
        return 'hot'  # -0.02 xG adjustment
    elif form_score < -2:
        return 'cold'  # +0.02 xG adjustment
    else:
        return 'normal'
```

## Model Architecture

### Option 1: Adjustment Layer
```python
# Simple adjustment on top of base model
final_xg = base_xg * goalie_quality_multiplier + goalie_specific_adjustment
```

### Option 2: Ensemble Approach
```python
# Separate models by goalie tier
elite_goalie_model = train_on_elite_goalies()
average_goalie_model = train_on_average_goalies()
backup_goalie_model = train_on_backups()

# Weighted prediction
if goalie_tier == 'elite':
    xg = elite_goalie_model.predict(shot) * 0.7 + base_model.predict(shot) * 0.3
```

### Option 3: Full Integration
```python
# Goalie features as part of main model
all_features = shot_features + goalie_embeddings + matchup_features
final_model = train_on_all_features(all_features)
```

## Expected Impact

### Without Goalie-Specific Features
- All goalies treated equally
- Vasilevskiy = AHL backup
- AUC ~0.75

### With Basic Goalie Quality
- Save percentage adjustment
- General quality tiers
- AUC ~0.78

### With Full Goalie Modeling
- Individual strengths/weaknesses
- Matchup history
- Fatigue response profiles
- Movement vulnerabilities
- Current form tracking
- AUC ~0.82-0.85

## Validation Tests

### 1. Elite vs Average Goalies
```python
# Elite goalies should suppress xG
elite_goalies = ['Vasilevskiy', 'Shesterkin', 'Hellebuyck']
elite_shots = shots[shots['goalie_name'].isin(elite_goalies)]
average_shots = shots[~shots['goalie_name'].isin(elite_goalies)]

print(f"Goals vs Elite: {elite_shots['is_goal'].mean():.3f}")
print(f"Goals vs Average: {average_shots['is_goal'].mean():.3f}")
```

### 2. Goalie Consistency
```python
# Model should show consistent goalie effects
goalie_effects = {}
for goalie in shots['goalie_id'].unique():
    goalie_shots = shots[shots['goalie_id'] == goalie]
    if len(goalie_shots) > 100:
        observed = goalie_shots['is_goal'].mean()
        expected = goalie_shots['xG'].mean()
        goalie_effects[goalie] = observed - expected

# Effects should be stable across seasons
```

### 3. Situation-Specific Performance
```python
# Some goalies better on breakaways, others on scrambles
for situation in ['breakaway', 'rebound', 'screened', 'royal_road']:
    situation_performance = shots[shots[f'is_{situation}']].groupby('goalie_id').agg({
        'is_goal': 'mean',
        'count': 'size'
    })
    
    # Should see meaningful variance between goalies
```

## Production Considerations

```python
class GoalieAwareXGPredictor:
    def __init__(self):
        self.load_goalie_profiles()
        self.load_current_form()
        
    def predict(self, shot):
        # Get base xG
        base_xg = self.base_model.predict(shot)
        
        # Apply goalie adjustments
        goalie_quality = self.get_goalie_quality(shot.goalie_id)
        matchup_history = self.get_matchup_adjustment(shot.shooter_id, shot.goalie_id)
        current_form = self.get_form_adjustment(shot.goalie_id, shot.game_date)
        fatigue_impact = self.get_fatigue_adjustment(shot.goalie_id, shot.workload)
        
        # Combine adjustments
        adjusted_xg = base_xg * goalie_quality + matchup_history + current_form + fatigue_impact
        
        return np.clip(adjusted_xg, 0.01, 0.99)
```