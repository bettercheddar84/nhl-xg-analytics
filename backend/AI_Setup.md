## HEIGHT TIERS (by position)

### Forwards
- Small: <5'11" (speed/agility advantage)
- Medium: 5'11"-6'1" (balanced)
- Large: >6'1" (reach/power advantage)

### Defensemen  
- Small: <6'0" (mobility)
- Medium: 6'0"-6'2" (balanced)
- Large: >6'2" (reach/clearance)

### Goalies
- Small: <6'2" (lateral speed)
- Medium: 6'2"-6'4" (balanced)
- Large: >6'4" (coverage)

## PASSING DATA LIMITATIONS

### What We Have:
- assist1_id (last pass)
- assist2_id (second-to-last pass)
- prev_event_type (could be "pass")
- time_since_prev_event

### What We DON'T Have:
- Pass distance/length
- Total passes in sequence
- Pass locations (x,y)
- Pass type (cross-ice, drop, etc.)

### Possible Derivations:
```python
# Quick plays (likely fewer passes)
is_quick_play = time_since_faceoff < 10
is_one_timer = time_since_prev_event < 2 and prev_event_type == "pass"

# Multi-pass plays (both assists present)
has_full_passing_play = pd.notna(assist1_id) and pd.notna(assist2_id)

# Defensive breakdown (D-to-D assist suggests cycling)
is_d_to_d_play = (assist1_position == 'D' and assist2_position == 'D')
To Get Full Passing Data:
Would need to re-parse play-by-play:

For each goal, walk backwards through events
Count passes until possession change
Calculate pass distances from x,y coordinates
Identify pass types (stretch, cycle, etc.)

Worth adding to data collection?

The height tiers should be position-specific since a 6'0" forward is average but a 6'0" defenseman is small. The passing limitation is real - we only know the last two passers, not the full sequence.RetryRWyes i think this is the last partcan you please combine this with the final training md script?Editmarkdown# NHL Expected Goals (xG) Model - Complete Training Architecture

## Data Sources & Relationships

### 1. CORE SHOT DATA (313,244 records)
**File:** `data/nhl/raw/nhl_shots_2024-10-01_to_2025-04-15.csv`

Primary features for each shot:
- **Shot Context**
 - x_coord, y_coord (location)
 - shot_distance, shot_angle (calculated)
 - shot_type (wrist, slap, snap, etc.)
 - period, time_remaining
 
- **Player IDs** (link to quality metrics)
 - shooter_id → Player quality
 - goalie_id → Goalie quality
 - assist1_id → Playmaker quality
 - assist2_id → Secondary assist quality

- **Game State**
 - score_differential
 - is_powerplay, is_shorthanded
 - empty_net
 - home/away status

- **Shot Patterns**
 - is_rebound (within 3 seconds)
 - is_rush (quick transition)
 - time_since_faceoff
 - is_off_zone_faceoff (offensive zone win)

- **Target Variable**
 - is_goal (0 or 1)

### 2. PLAYER QUALITY METRICS (1,016 players)
**Files:** `data/nhl/players/{player_id}.json`

For each player:
- **Physical Attributes**
 - height (inches) - impacts shot/save ability
 - weight - physical presence
 - shoots/catches (L/R) - handedness

- **Current Season Performance**
 - goals, assists, points
 - plusMinus (key indicator)
 - shootingPctg (for shooters)
 - savePctg (for goalies)
 - gamesPlayed

### 3. ON-ICE CONTEXT (16,140 goals)
**File:** `data/nhl/shifts/goals_with_on_ice_fixed.csv`

For each goal:
- offensive_on_ice[] - all attacking players
- defensive_on_ice[] - all defending players

### 4. PLAY-BY-PLAY SEQUENCES (TO BE EXTRACTED)
**Source:** Re-parse game files for passing sequences

For each goal, walk backwards to extract:
- Total passes in sequence
- Pass distances (from x,y coords)
- Time between passes
- Pass types (cross-ice, drop, cycle)

## Enhanced Feature Engineering

### HEIGHT TIERS (Position-Specific)

#### Forwards
- Small: <5'11" (speed/agility advantage)
- Medium: 5'11"-6'1" (balanced)
- Large: >6'1" (reach/power advantage)

#### Defensemen  
- Small: <6'0" (mobility)
- Medium: 6'0"-6'2" (balanced)
- Large: >6'2" (reach/clearance)

#### Goalies
- Small: <6'2" (lateral speed)
- Medium: 6'2"-6'4" (balanced)
- Large: >6'4" (coverage)

### SHOOTER FEATURES
- **Elite Status**: Top 20 in league by points
- **Height Tier**: Position-specific categorization
- **Shooting Volume**: Total shots taken
- **Fast Break Liability**: Goals against within 30s of missed shot
- **Plus/Minus**: Overall ice impact
- **Faceoff Conversion**: Goals within 20s of offensive zone faceoff

### GOALIE FEATURES
- **Height Tier**: Small/Medium/Large
- **Workload** (Fatigue indicators):
 - Saves in last 60 seconds
 - Saves in last 30 seconds  
 - Saves in last 10 seconds
- **Performance Metrics**:
 - Goals Against Average (GAA)
 - Save Percentage
 - Power Play Save %

### ASSIST FEATURES

#### Primary Assist (Assist1)
- Plus/Minus factor
- Height tier
- Average shift length when scoring/scored on
- Play creation type:
 - Faceoff → Goal within 20s
 - Created rebound (shot for pads)
 - Recovery from missed shot

#### Secondary Assist (Assist2)  
- Position (D vs F)
- Plus/Minus factor
- Height tier
- Average shift length patterns

### PASSING SEQUENCE FEATURES (NEW)
- **Passing Metrics**:
 - Total passes before goal
 - Average pass distance
 - Longest pass in sequence
 - Time from first pass to goal
- **Pass Types**:
 - Cross-ice passes (dangerous)
 - Drop passes (deceptive)
 - Cycle passes (possession)
- **Sequence Patterns**:
 - Quick strike (≤2 passes)
 - Sustained pressure (>5 passes)
 - D-to-D-to-F progression

## Calculated Features

### Matchup Scores
```python
# Height advantages
shooter_height_advantage = shooter_height_tier - goalie_height_tier
assist_height_advantage = assist1_height_tier - avg_defender_height_tier

# Elite vs Average
elite_vs_average_goalie = shooter_elite * (1 - goalie_save_pct)

# Fatigue factors
goalie_fatigue = saves_60s * 0.5 + saves_30s * 0.3 + saves_10s * 0.2
defender_avg_shift_length = mean([shift_length for d in defenders_on_ice])

# Play quality
passing_complexity = total_passes * avg_pass_distance
quick_strike_bonus = 1.3 if total_passes <= 2 else 1.0
Team Context
python# Defensive liability
defensive_weakness = mean([d.plus_minus for d in defenders_on_ice])
negative_defender_count = sum([1 for d in defenders_on_ice if d.plus_minus < 0])

# Offensive pressure
offensive_quality = mean([p.plus_minus for p in offensive_on_ice])
elite_players_on_ice = sum([1 for p in offensive_on_ice if p.points > top_20_threshold])
Neural Network Architecture
Input Layer (~85 features)

Base shot features (15)
Shooter features (12)
Goalie features (10)
Assist1 features (10)
Assist2 features (8)
Passing sequence (10)
Game state (10)
Team context (10)

Architecture
pythonmodel = Sequential([
    Dense(512, activation='relu', input_dim=85),
    BatchNormalization(),
    Dropout(0.3),
    
    Dense(256, activation='relu'),
    BatchNormalization(),
    Dropout(0.2),
    
    Dense(128, activation='relu'),
    BatchNormalization(),
    Dropout(0.2),
    
    Dense(64, activation='relu'),
    Dense(32, activation='relu'),
    
    Dense(1, activation='sigmoid')  # Goal probability
])
Training Strategy

Optimizer: Adam with learning rate scheduling
Loss: Binary crossentropy with class weights (goals are rare)
Validation: Time-based split (last month as test)
Batch size: 512 (optimized for P16 GPU)

Key Hypotheses to Test

Height Matchups: Do height advantages significantly impact xG?
Elite Persistence: Do elite shooters maintain high xG against elite goalies?
Fatigue Factor: Does goalie workload (recent saves) increase xG?
Negative Defenders: Do negative +/- defenders create scoring chances?
Passing Complexity: Do more passes = higher xG or diminishing returns?
Quick Strikes: Are 1-2 pass plays more dangerous than sustained pressure?
Position Matchups: Are D-to-F assists more dangerous than F-to-F?
Shift Length: Is there an optimal shift duration before performance drops?

Implementation Pipeline
Phase 1: Data Preparation

Extract passing sequences from play-by-play
Calculate player height tiers
Compute goalie workload metrics
Generate all matchup features

Phase 2: Feature Engineering

Create elite player classifications
Calculate all derived features
Normalize continuous variables
One-hot encode categorical features

Phase 3: Model Training

Split data temporally
Train neural network with GPU optimization
Evaluate feature importance
Generate xG predictions

Phase 4: Analysis

Which features matter most?
How do elite players break the model?
What creates "impossible" goals?
Where do coaching strategies show up?

Output

xG probability for every shot
Feature importance rankings
Player quality impact analysis
Coaching insights (optimal matchups, shift lengths, etc.)

# Missing Datasets & Data Locations

## 1. PASSING SEQUENCES (NOT YET BUILT)
**Need to create:** `data/nhl/processed/passing_sequences.csv`

Extract from existing play-by-play by walking backwards from each goal:
```python
# For each goal, extract:
goal_id | total_passes | avg_pass_distance | longest_pass | time_first_to_last_pass | pass_types
Source data: Would need to re-parse game files or use existing shift JSONs
2. GOALIE WORKLOAD (NOT YET BUILT)
Need to create: data/nhl/processed/goalie_workload.csv
Calculate saves before each goal:
python# For each goal:
goal_id | goalie_id | saves_last_10s | saves_last_30s | saves_last_60s
Source data: Use existing shots CSV - count shot-on-goal events
3. PLAYER HEIGHT TIERS (NOT YET BUILT)
Need to create: data/nhl/processed/player_tiers.csv
pythonplayer_id | position | height | height_tier | elite_status | plus_minus_tier
Source data:

Heights from: data/nhl/players/*.json
Stats from: data/nhl/season_stats/all_players_202425.json

4. SHIFT PATTERNS (NOT YET BUILT)
Need to create: data/nhl/processed/player_shift_patterns.csv
Average shift lengths when scoring vs scored on:
pythonplayer_id | avg_shift_length_scoring | avg_shift_length_scored_on | total_goals_for | total_goals_against
Source data: data/nhl/shifts/*.json files
Current Data Locations
✅ HAVE THESE:
data/
├── nhl/
│   ├── raw/
│   │   └── nhl_shots_2024-10-01_to_2025-04-15.csv (313k shots)
│   ├── players/
│   │   ├── 8471675.json (Crosby example)
│   │   └── ... (1,016 player files with names, height, stats)
│   ├── season_stats/
│   │   ├── all_players_202425.json (stats without names)
│   │   ├── skaters_202425.json (top 25)
│   │   └── goalies_202425.json (top 25)
│   ├── shifts/
│   │   ├── 2024020001.json through 2024021312.json (1,312 games)
│   │   └── goals_with_on_ice_fixed.csv (on-ice players per goal)
│   └── player_names.json (ID to name lookup - if created)
❌ NEED TO BUILD:
data/
└── nhl/
    └── processed/
        ├── passing_sequences.csv
        ├── goalie_workload.csv
        ├── player_tiers.csv
        ├── player_shift_patterns.csv
        └── training_data_complete.csv (final merged dataset)
Build Scripts Needed
1. scripts/build_goalie_workload.py
python# Read shots CSV
# For each goal, count saves in time windows
# Output: goalie workload metrics
2. scripts/build_player_tiers.py
python# Read player JSONs for height
# Read season stats for performance
# Classify into tiers by position
# Output: player classifications
3. scripts/build_shift_patterns.py
python# Read shift JSONs
# Match to goals_with_on_ice
# Calculate avg shift lengths
# Output: shift pattern metrics
4. scripts/extract_passing_sequences.py
python# This is complex - need play-by-play data
# Either re-fetch games or parse from somewhere
# Extract pass counts and distances
5. scripts/merge_training_data.py
python# Merge all datasets on shot_id/goal_id
# Create final training dataset
# Handle missing values
# Output: training_data_complete.csv
